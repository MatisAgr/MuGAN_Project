import os
import glob
import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np
import pickle

from music21 import converter, instrument, note, chord
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


def collect_midi_files(data_dir: str, max_files: int = 10) -> list:
    """
    data_dir: chemin vers le dossier contenant les fichiers MIDI
    max_files: nombre maximum de fichiers à traiter (None = tous les fichiers)
    """
    midi_patterns = ['**/*.midi', '**/*.mid', '**/*.MIDI', '**/*.MID']
    midi_files = []
    
    for pattern in midi_patterns:
        midi_files.extend(glob.glob(os.path.join(data_dir, pattern), recursive=True))
    
    # Supprimer les doublons
    midi_files = list(set(midi_files))
    
    if max_files is not None:
        midi_files = midi_files[:max_files]
        print(f"{len(midi_files)} midi files found (limited to {max_files} for test)")
    else:
        print(f"{len(midi_files)} midi files found (full processing)")
    
    return midi_files


def extract_notes_from_midi(midi_path: str) -> list:
    """
    midi_path: chemin vers le fichier MIDI
    """
    try:
        score = converter.parse(midi_path)
        notes_list = []
        
        for element in score.recurse().notesAndRests:
            if isinstance(element, note.Note):
                notes_list.append({
                    'pitch': element.pitch.midi,
                    'offset': element.offset,
                    'duration': element.quarterLength,
                    'velocity': getattr(element.volume, 'velocity', 64)
                })
            elif isinstance(element, chord.Chord):
                notes_list.append({
                    'pitch': element.pitches[0].midi,
                    'offset': element.offset,
                    'duration': element.quarterLength,
                    'velocity': getattr(element.volume, 'velocity', 64)
                })
        
        return notes_list
    except Exception as e:
        print(f"error reading {midi_path}: {e}")
        return []


def extract_sequences(notes_list: list, sequence_length: int = 32) -> list:
    """
    notes_list: liste des notes extraites
    sequence_length: longueur de chaque séquence
    Quantise la durée en 5 classes: [0.25, 0.5, 1.0, 2.0, 4.0]
    """
    def quantize_duration(duration):
        if duration < 0.375:
            return 0
        elif duration < 0.75:
            return 1
        elif duration < 1.5:
            return 2
        elif duration < 3.0:
            return 3
        else:
            return 4
    
    sequences = []
    
    if len(notes_list) < sequence_length:
        pairs = [[n['pitch'], quantize_duration(n['duration'])] for n in notes_list]
        pairs.extend([[-1, 0]] * (sequence_length - len(pairs)))
        sequences.append(pairs)
    else:
        for i in range(len(notes_list) - sequence_length + 1):
            sequence = [[n['pitch'], quantize_duration(n['duration'])] for n in notes_list[i:i+sequence_length]]
            sequences.append(sequence)
    
    return sequences


def preprocess_dataset(data_dir: str, 
                       output_dir: str,
                       sequence_length: int = 32,
                       train_split: float = 0.9,
                       progress_callback=None,
                       max_files: int = 10):
    """
    data_dir: dossier contenant les fichiers MIDI
    output_dir: dossier de sortie pour les données prétraitées
    sequence_length: longueur des séquences de notes
    train_split: proportion pour l'entraînement (reste = validation)
    progress_callback: fonction appelée avec (progress: int, message: str)
    max_files: nombre maximum de fichiers à traiter
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
    all_pitches = []
    
    print("\nprocessing midi files...")
    update_progress(10, f"Extracting notes from {len(midi_files)} MIDI files...")
    for idx, midi_path in enumerate(midi_files):
        notes_list = extract_notes_from_midi(midi_path)
        
        if len(notes_list) == 0:
            continue
        
        sequences = extract_sequences(notes_list, sequence_length)
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
        "min_pitch": int(np.min(all_pitches)),
        "max_pitch": int(np.max(all_pitches)),
        "avg_pitch": float(np.mean(all_pitches)),
        "total_notes": len(all_pitches)
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
                        help="folder containing midi files")
    parser.add_argument("--output_dir", type=str, default=str(PROCESSED_DIR),
                        help="output folder for preprocessed data")
    parser.add_argument("--sequence_length", type=int, default=32,
                        help="length of note sequences")
    parser.add_argument("--train_split", type=float, default=0.9,
                        help="proportion for training")
    
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

