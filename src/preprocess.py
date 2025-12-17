"""
Script de prétraitement des fichiers MIDI pour entraînement.
Convertit les fichiers MIDI en données exploitables avec Music21.
"""

import os
import glob
import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np
import pickle

# Music21 pour manipulation MIDI
from music21 import converter, instrument, note, chord

# Déterminer le dossier du projet (parent du dossier src)
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


def collect_midi_files(data_dir: str, max_files: int = 10) -> list:
    """
    Collecte tous les fichiers MIDI dans le répertoire data et ses sous-dossiers.
    
    Args:
        data_dir: Chemin vers le dossier contenant les fichiers MIDI
        max_files: Nombre maximum de fichiers à traiter (None = tous les fichiers)
        
    Returns:
        Liste des chemins vers les fichiers MIDI
    """
    midi_patterns = ['**/*.midi', '**/*.mid', '**/*.MIDI', '**/*.MID']
    midi_files = []
    
    for pattern in midi_patterns:
        midi_files.extend(glob.glob(os.path.join(data_dir, pattern), recursive=True))
    
    # Supprimer les doublons
    midi_files = list(set(midi_files))
    
    # Limiter si demandé (max_files=None pour tous les fichiers)
    if max_files is not None:
        midi_files = midi_files[:max_files]
        print(f"📁 {len(midi_files)} fichiers MIDI trouvés (limité à {max_files} pour test)")
    else:
        print(f"� {len(midi_files)} fichiers MIDI trouvés (traitement complet)")
    
    return midi_files


def extract_notes_from_midi(midi_path: str) -> list:
    """
    Extrait les notes d'un fichier MIDI.
    
    Args:
        midi_path: Chemin vers le fichier MIDI
        
    Returns:
        Liste de dictionnaires avec les informations des notes
    """
    try:
        score = converter.parse(midi_path)
        notes_list = []
        
        # Parcourir tous les éléments musicaux
        for element in score.recurse().notesAndRests:
            if isinstance(element, note.Note):
                notes_list.append({
                    'pitch': element.pitch.midi,
                    'offset': element.offset,
                    'duration': element.quarterLength,
                    'velocity': getattr(element.volume, 'velocity', 64)
                })
            elif isinstance(element, chord.Chord):
                # Pour les accords, on prend la note la plus basse
                notes_list.append({
                    'pitch': element.pitches[0].midi,
                    'offset': element.offset,
                    'duration': element.quarterLength,
                    'velocity': getattr(element.volume, 'velocity', 64)
                })
        
        return notes_list
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture de {midi_path}: {e}")
        return []


def extract_sequences(notes_list: list, sequence_length: int = 32) -> list:
    """
    Divise une liste de notes en séquences pour l'entraînement.
    
    Args:
        notes_list: Liste des notes extraites
        sequence_length: Longueur de chaque séquence
        
    Returns:
        Liste de séquences (chacune est une liste de pitch)
    """
    sequences = []
    
    if len(notes_list) < sequence_length:
        # Si la séquence est trop courte, la compléter avec des silences (pitch=-1)
        pitches = [n['pitch'] for n in notes_list]
        pitches.extend([-1] * (sequence_length - len(pitches)))
        sequences.append(pitches)
    else:
        # Créer des séquences avec chevauchement
        for i in range(len(notes_list) - sequence_length + 1):
            sequence = [n['pitch'] for n in notes_list[i:i+sequence_length]]
            sequences.append(sequence)
    
    return sequences


def preprocess_dataset(data_dir: str, 
                       output_dir: str,
                       sequence_length: int = 32,
                       train_split: float = 0.9):
    """
    Pipeline complet de prétraitement des fichiers MIDI.
    
    Args:
        data_dir: Dossier contenant les fichiers MIDI
        output_dir: Dossier de sortie pour les données prétraitées
        sequence_length: Longueur des séquences de notes
        train_split: Proportion pour l'entraînement (reste = validation)
    """
    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Collecter les fichiers MIDI
    midi_files = collect_midi_files(data_dir)
    
    if len(midi_files) == 0:
        print("❌ Aucun fichier MIDI trouvé!")
        return
    
    all_sequences = []
    all_pitches = []
    
    print("\n🎹 Traitement des fichiers MIDI...")
    for midi_path in tqdm(midi_files, desc="Extraction des notes"):
        # Extraire les notes
        notes_list = extract_notes_from_midi(midi_path)
        
        if len(notes_list) == 0:
            continue
        
        # Extraire les séquences
        sequences = extract_sequences(notes_list, sequence_length)
        all_sequences.extend(sequences)
        
        # Collecter les pitch pour les statistiques
        all_pitches.extend([n['pitch'] for n in notes_list])
    
    print(f"\n✅ Total: {len(all_sequences)} séquences créées")
    
    if len(all_sequences) == 0:
        print("❌ Aucune séquence valide créée!")
        return
    
    # Convertir en numpy arrays
    all_sequences = np.array(all_sequences, dtype=np.int32)
    
    # Mélanger les séquences
    np.random.shuffle(all_sequences)
    
    # Diviser en train/validation
    split_idx = int(len(all_sequences) * train_split)
    train_sequences = all_sequences[:split_idx]
    val_sequences = all_sequences[split_idx:]
    
    # Sauvegarder les données
    train_path = os.path.join(output_dir, "train_sequences.npy")
    val_path = os.path.join(output_dir, "validation_sequences.npy")
    
    np.save(train_path, train_sequences)
    np.save(val_path, val_sequences)
    
    print(f"💾 Données d'entraînement: {train_path} ({train_sequences.shape})")
    print(f"💾 Données de validation: {val_path} ({val_sequences.shape})")
    
    # Sauvegarder les statistiques
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
    
    print(f"\n📊 Statistiques sauvegardées dans {stats_path}")
    print("✅ Prétraitement terminé!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prétraitement des fichiers MIDI")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR),
                        help="Dossier contenant les fichiers MIDI")
    parser.add_argument("--output_dir", type=str, default=str(PROCESSED_DIR),
                        help="Dossier de sortie pour les données prétraitées")
    parser.add_argument("--sequence_length", type=int, default=32,
                        help="Longueur des séquences de notes")
    parser.add_argument("--train_split", type=float, default=0.9,
                        help="Proportion pour l'entraînement")
    
    args = parser.parse_args()
    
    print(f"📁 Dossier du projet: {PROJECT_DIR}")
    print(f"📁 Dossier des données: {args.data_dir}")
    print(f"📁 Dossier de sortie: {args.output_dir}\n")
    
    preprocess_dataset(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        sequence_length=args.sequence_length,
        train_split=args.train_split
    )

