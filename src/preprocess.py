import os
import glob
import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np

from music21 import converter, note, chord, stream
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

MAX_PITCHES = 4
NUM_DURATION_CLASSES = 8
NUM_TIME_SHIFT_CLASSES = 16


def collect_midi_files(data_dir: str, max_files: int = 10) -> list:
    midi_patterns = ['**/*.midi', '**/*.mid', '**/*.MIDI', '**/*.MID']
    midi_files = []
    
    for pattern in midi_patterns:
        midi_files.extend(glob.glob(os.path.join(data_dir, pattern), recursive=True))
    
    midi_files = list(set(midi_files))
    
    if max_files is not None:
        midi_files = midi_files[:max_files]
        print(f"{len(midi_files)} midi files found (limited to {max_files} for test)")
    else:
        print(f"{len(midi_files)} midi files found (full processing)")
    
    return midi_files


def quantize_duration(duration: float) -> int:
    boundaries = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    for i, b in enumerate(boundaries):
        if duration < b * 1.5:
            return i
    return len(boundaries)


def quantize_time_shift(time_shift: float) -> int:
    if time_shift < 0.0625:
        return 0
    boundaries = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
    for i, b in enumerate(boundaries):
        if time_shift < b * 1.5:
            return i + 1
    return NUM_TIME_SHIFT_CLASSES - 1


def extract_events_from_midi(midi_path: str) -> list:
    try:
        score = converter.parse(midi_path)
        events = []
        
        all_notes = []
        for element in score.recurse().notesAndRests:
            if isinstance(element, note.Note):
                all_notes.append({
                    'pitches': [element.pitch.midi],
                    'offset': float(element.offset),
                    'duration': float(element.quarterLength),
                    'is_rest': False
                })
            elif isinstance(element, chord.Chord):
                pitches = sorted([p.midi for p in element.pitches])[:MAX_PITCHES]
                all_notes.append({
                    'pitches': pitches,
                    'offset': float(element.offset),
                    'duration': float(element.quarterLength),
                    'is_rest': False
                })
            elif isinstance(element, note.Rest) and element.quarterLength >= 0.25:
                all_notes.append({
                    'pitches': [],
                    'offset': float(element.offset),
                    'duration': float(element.quarterLength),
                    'is_rest': True
                })
        
        all_notes.sort(key=lambda x: x['offset'])
        
        prev_offset = 0.0
        for n in all_notes:
            time_shift = n['offset'] - prev_offset
            
            pitch_vector = [0] * MAX_PITCHES
            if n['is_rest']:
                pitch_vector = [129] * MAX_PITCHES
            else:
                for i, p in enumerate(n['pitches'][:MAX_PITCHES]):
                    pitch_vector[i] = p
                for i in range(len(n['pitches']), MAX_PITCHES):
                    pitch_vector[i] = 128
            
            event = pitch_vector + [
                quantize_duration(n['duration']),
                quantize_time_shift(time_shift)
            ]
            events.append(event)
            prev_offset = n['offset']
        
        return events
    except Exception as e:
        print(f"error reading {midi_path}: {e}")
        return []


def extract_sequences(events: list, sequence_length: int = 32) -> list:
    sequences = []
    event_size = MAX_PITCHES + 2
    
    if len(events) < sequence_length:
        padded = events + [[128] * MAX_PITCHES + [0, 0]] * (sequence_length - len(events))
        sequences.append(padded)
    else:
        for i in range(len(events) - sequence_length + 1):
            sequences.append(events[i:i+sequence_length])
    
    return sequences


def preprocess_dataset(data_dir: str, 
                       output_dir: str,
                       sequence_length: int = 32,
                       train_split: float = 0.9):
    os.makedirs(output_dir, exist_ok=True)
    
    midi_files = collect_midi_files(data_dir)
    
    if len(midi_files) == 0:
        print("no midi files found")
        return
    
    all_sequences = []
    
    print("\nprocessing midi files")
    for midi_path in tqdm(midi_files, desc="extracting events"):
        events = extract_events_from_midi(midi_path)
        
        if len(events) == 0:
            continue
        
        sequences = extract_sequences(events, sequence_length)
        all_sequences.extend(sequences)
    
    print(f"\ntotal: {len(all_sequences)} sequences created")
    
    if len(all_sequences) == 0:
        print("no valid sequences created")
        return
    
    all_sequences = np.array(all_sequences, dtype=np.int32)
    
    np.random.shuffle(all_sequences)
    
    split_idx = int(len(all_sequences) * train_split)
    train_sequences = all_sequences[:split_idx]
    val_sequences = all_sequences[split_idx:]
    
    train_path = os.path.join(output_dir, "train_sequences.npy")
    val_path = os.path.join(output_dir, "validation_sequences.npy")
    
    np.save(train_path, train_sequences)
    np.save(val_path, val_sequences)
    
    print(f"training data: {train_path} (shape: {train_sequences.shape})")
    print(f"validation data: {val_path} (shape: {val_sequences.shape})")
    
    stats = {
        "total_midi_files": len(midi_files),
        "total_sequences": len(all_sequences),
        "train_sequences": len(train_sequences),
        "val_sequences": len(val_sequences),
        "sequence_length": sequence_length,
        "event_size": MAX_PITCHES + 2,
        "max_pitches_per_event": MAX_PITCHES,
        "num_duration_classes": NUM_DURATION_CLASSES,
        "num_time_shift_classes": NUM_TIME_SHIFT_CLASSES
    }
    
    stats_path = os.path.join(output_dir, "stats.txt")
    with open(stats_path, 'w') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    
    print(f"\nstats saved in {stats_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocessing of MIDI files")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR))
    parser.add_argument("--output_dir", type=str, default=str(PROCESSED_DIR))
    parser.add_argument("--sequence_length", type=int, default=32)
    parser.add_argument("--train_split", type=float, default=0.9)
    
    args = parser.parse_args()
    
    print(f"project folder: {PROJECT_DIR}")
    print(f"data folder: {args.data_dir}")
    print(f"output folder: {args.output_dir}\n")
    
    preprocess_dataset(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        sequence_length=args.sequence_length,
        train_split=args.train_split
    )
