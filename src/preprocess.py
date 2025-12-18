import os
import glob
import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np

from music21 import converter, note, chord, stream
from config import MAX_PITCHES, NUM_DURATION_CLASSES, NUM_TIME_SHIFT_CLASSES

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


def collect_midi_files(data_dir: str, max_files: int = 10) -> list:
    """
    Collect all MIDI files from directory and subdirectories.
    
    Searches for files with extensions: .midi, .mid (case-insensitive).
    Removes duplicates before limiting to max_files.
    
    Args:
        data_dir: Root directory to search for MIDI files.
        max_files: Maximum number of files to return. If None, returns all found.
        
    Returns:
        List of absolute paths to MIDI files.
    """
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
    """
    Quantize duration to nearest class (0-7).
    
    Maps continuous duration to discrete classes:
    - 0: <= 0.1875 quarter notes
    - 1: < 0.375
    - 2: < 0.75
    - 3: < 1.5
    - 4: < 3.0
    - 5: < 6.0
    - 6: < 12.0
    - 7: >= 12.0
    
    Args:
        duration: Duration in quarter notes.
        
    Returns:
        Class index 0-7.
    """
    boundaries = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
    for i, b in enumerate(boundaries):
        if duration < b * 1.5:
            return i
    return len(boundaries)


def quantize_time_shift(time_shift: float) -> int:
    """
    Quantize time shift (gap between notes) to nearest class (0-8).
    
    Maps continuous time shift to discrete classes:
    - 0: < 0.0625 quarter notes (silence suppressed)
    - 1: < 0.1875
    - 2: < 0.375
    - 3: < 0.75
    - 4: < 1.5
    - 5: < 3.0
    - 6: < 6.0
    - 7: < 12.0
    - 8: >= 12.0
    
    Args:
        time_shift: Time gap in quarter notes.
        
    Returns:
        Class index 0-8.
    """
    if time_shift < 0.0625:
        return 0
    boundaries = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
    for i, b in enumerate(boundaries):
        if time_shift < b * 1.5:
            return i + 1
    return NUM_TIME_SHIFT_CLASSES - 1


def extract_events_from_midi(midi_path: str) -> list:
    """
    Extract music events from a MIDI file.
    
    Parses MIDI file and extracts all notes, chords, and rests.
    Creates event list with format: [pitch_0, pitch_1, pitch_2, pitch_3, duration_class, time_shift_class]
    
    Pitch encoding:
    - 0-127: valid MIDI pitches
    - 128: padding (no pitch at this position in chord)
    - 129: rest event (all pitches = 129)
    
    Args:
        midi_path: Path to MIDI file.
        
    Returns:
        List of events, empty list if parsing failed.
    """
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
                # Filter out very short rests (< 0.25 quarter length) which represent
                # insignificant pauses and may introduce noise in the training data
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
    """
    Extract fixed-length sequences from a list of events.
    
    If events list is shorter than sequence_length, pads with padding events.
    Otherwise, creates overlapping sequences using sliding window.
    
    Args:
        events: List of events (each event is [pitch_0, pitch_1, pitch_2, pitch_3, duration, time_shift]).
        sequence_length: Target length for each sequence.
        
    Returns:
        List of sequences, each of length sequence_length.
    """
    sequences = []
    
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
                       train_split: float = 0.9,
                       progress_callback=None,
                       max_files: int = 10):
    """
    Preprocess all MIDI files in a directory into training sequences.
    
    Workflow:
    1. Collect all MIDI files from data_dir
    2. Extract events from each file
    3. Create fixed-length sequences
    4. Split into training/validation sets
    5. Save as .npy files and generate statistics
    
    Args:
        data_dir: Directory containing MIDI files.
        output_dir: Directory to save preprocessed data.
        sequence_length: Length of event sequences (default: 32).
        train_split: Fraction for training (rest goes to validation, default: 0.9).
    """
    def update_progress(progress, message):
        if progress_callback:
            progress_callback(progress, message)
    
    os.makedirs(output_dir, exist_ok=True)
    
    update_progress(5, "Collecting MIDI files...")
    midi_files = collect_midi_files(data_dir, max_files=max_files)
    
    if len(midi_files) == 0:
        print("no midi files found!")
        update_progress(0, "Error: no midi files found!")
        return
    
    all_sequences = []
    
    print("\nprocessing midi files...")
    update_progress(10, f"Extracting notes from {len(midi_files)} MIDI files...")
    for idx, midi_path in enumerate(midi_files):
        notes_list = extract_notes_from_midi(midi_path)
        
        if len(events) == 0:
            continue
        
        sequences = extract_sequences(events, sequence_length)
        all_sequences.extend(sequences)
        
        all_pitches.extend([n['pitch'] for n in notes_list])
        
        progress = 10 + int((idx / len(midi_files)) * 50)
        update_progress(progress, f"Processing file {idx + 1}/{len(midi_files)}: {os.path.basename(midi_path)}")
    
    print(f"\ntotal: {len(all_sequences)} sequences created")
    
    if len(all_sequences) == 0:
        print("no valid sequences created!")
        update_progress(0, "Error: no valid sequences created!")
        return
    
    update_progress(65, f"Converting {len(all_sequences)} sequences to numpy arrays...")
    all_sequences = np.array(all_sequences, dtype=np.float32)
    
    update_progress(75, "Shuffling and splitting data...")
    np.random.shuffle(all_sequences)
    
    split_idx = int(len(all_sequences) * train_split)
    train_sequences = all_sequences[:split_idx]
    val_sequences = all_sequences[split_idx:]
    
    update_progress(85, f"Saving {len(train_sequences)} training sequences...")
    train_path = os.path.join(output_dir, "train_sequences.npy")
    val_path = os.path.join(output_dir, "validation_sequences.npy")
    
    np.save(train_path, train_sequences)
    np.save(val_path, val_sequences)
    
    print(f"training data: {train_path} (shape: {train_sequences.shape})")
    print(f"validation data: {val_path} (shape: {val_sequences.shape})")
    
    update_progress(95, "Saving statistics...")
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
    print("preprocessing complete!")
    update_progress(100, "Preprocessing completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocessing of MIDI files")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR),
                        help="directory containing MIDI files (default: data/)")
    parser.add_argument("--output_dir", type=str, default=str(PROCESSED_DIR),
                        help="directory to save preprocessed data (default: data/processed/)")
    parser.add_argument("--sequence_length", type=int, default=32,
                        help="length of event sequences (default: 32)")
    parser.add_argument("--train_split", type=float, default=0.9,
                        help="fraction of data to use for training (default: 0.9)")
    
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
