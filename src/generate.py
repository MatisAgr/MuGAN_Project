import os
import glob
import argparse
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras

from music21 import stream, instrument, note, tempo, meter
PROJECT_DIR = Path(__file__).parent.parent
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"
GENERATED_DIR = PROJECT_DIR / "generated"


def find_latest_model(model_dir: str = None) -> str:
    """
    Trouve le meilleur modèle entraîné (best_model.h5).
    
    Args:
        model_dir: Dossier contenant les modèles (par défaut: MODELS_DIR du projet)
        
    Returns:
        Chemin vers le meilleur modèle
    """
    if model_dir is None:
        model_dir = str(MODELS_DIR)
    
    best_model_path = os.path.join(model_dir, "best_model.h5")
    
    if os.path.exists(best_model_path):
        return best_model_path
    
    final_model_path = os.path.join(model_dir, "model_final.h5")
    if os.path.exists(final_model_path):
        return final_model_path
    
    print(f"no model found in {model_dir}")
    print("   please run train.py first to train a model")
    return None


def load_model(model_path: str) -> keras.Model:
    """
    Charge le modèle sauvegardé.
    
    Args:
        model_path: Chemin vers le fichier .h5
        
    Returns:
        Modèle Keras chargé
    """
    try:
        model = keras.models.load_model(model_path)
        print(f"model loaded: {model_path}")
        return model
    except Exception as e:
        print(f"error loading model: {e}")
        return None


def generate_sequence(model: keras.Model,
                      seed_sequence: np.ndarray,
                      length: int = 128,
                      temperature: float = 0.7) -> list:
    """
    Génère une séquence de notes à partir d'une graine.
    
    Args:
        model: Modèle Keras entraîné
        seed_sequence: Séquence initiale (32 notes)
        length: Longueur totale à générer
        temperature: Contrôle de la créativité (0.5=conservateur, 1.0=normal, 1.5=créatif)
        
    Returns:
        Liste de notes générées
    """
    generated = list(seed_sequence)
    
    print(f"\ngeneration of {length} notes (temperature={temperature})...")
    
    for i in range(length - len(seed_sequence)):
        input_seq = np.array([generated[-32:]], dtype=np.int32)
        
        predictions = model.predict(input_seq, verbose=0)
        
        predictions = np.log(predictions + 1e-10) / temperature
        predictions = np.exp(predictions) / np.sum(np.exp(predictions))
        
        next_note = np.random.choice(predictions.shape[1], p=predictions[0])
        generated.append(int(next_note))
        
        if (i + 1) % 32 == 0:
            print(f"  {i + 1} / {length - len(seed_sequence)} notes generated")
    
    return generated


def sequence_to_midi(notes_sequence: list,
                     output_path: str,
                     tempo_bpm: int = 120,
                     instrument_name: str = "Piano") -> bool:
    """
    Convertit une séquence de notes en fichier MIDI.
    
    Args:
        notes_sequence: Liste de pitch (0-127)
        output_path: Chemin du fichier MIDI à générer
        tempo_bpm: Tempo en battements par minute
        instrument_name: Nom de l'instrument (Piano, Violin, etc.)
        
    Returns:
        True si succès, False sinon
    """
    try:
        # Créer un stream (partition musicale)
        score = stream.Score()
        part = stream.Part()
        
        # Ajouter l'instrument
        if instrument_name.lower() == "piano":
            part.append(instrument.Piano())
        elif instrument_name.lower() == "violin":
            part.append(instrument.Violin())
        elif instrument_name.lower() == "flute":
            part.append(instrument.Flute())
        else:
            part.append(instrument.Instrument())
        
        # Ajouter le tempo
        part.append(tempo.MetronomeMark(number=tempo_bpm))
        
        # Ajouter la signature temporelle (4/4)
        part.append(meter.TimeSignature('4/4'))
        
        duration = 0.5
        
        for pitch in notes_sequence:
            if pitch < 0 or pitch > 127:
                rest = note.Rest(quarterLength=duration)
                part.append(rest)
            else:
                n = note.Note(pitch, quarterLength=duration)
                part.append(n)
        
        score.append(part)
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        score.write('midi', fp=output_path)
        
        print(f"midi generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"error creating midi: {e}")
        return False


def generate_and_save(model_path: str,
                      output_dir: str = "../generated",
                      num_notes: int = 256,
                      temperature: float = 0.7,
                      num_samples: int = 1):
    """
    Pipeline complet: génère plusieurs MIDI et les sauvegarde.
    
    Args:
        model_path: Chemin vers le modèle entraîné
        output_dir: Dossier de sortie pour les MIDI générés
        num_notes: Nombre de notes à générer
        temperature: Contrôle de la créativité
        num_samples: Nombre de fichiers MIDI à générer
    """
    # Charger le modèle
    model = load_model(model_path)
    if model is None:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    seed = np.random.randint(0, 128, size=32, dtype=np.int32)
    
    print(f"\n{'='*60}")
    print(f"music generation")
    print(f"{'='*60}")
    print(f"configuration:")
    print(f"   - model: {model_path}")
    print(f"   - number of notes: {num_notes}")
    print(f"   - temperature: {temperature}")
    print(f"   - files to generate: {num_samples}")
    
    for i in range(num_samples):
        print(f"\n[{i+1}/{num_samples}] generation of file {i+1}...")
        
        sequence = generate_sequence(model, seed, num_notes, temperature)
        
        output_filename = f"generated_music_{i+1:03d}.midi"
        output_path = os.path.join(output_dir, output_filename)
        
        success = sequence_to_midi(sequence, output_path, tempo_bpm=120, instrument_name="Piano")
        
        if success:
            print(f"file {i+1} generated successfully!")
    
    print(f"\n{'='*60}")
    print(f"generation complete!")
    print(f"files saved in: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="music generation with trained model")
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR),
                        help="folder containing the trained model")
    parser.add_argument("--output_dir", type=str, default=str(GENERATED_DIR),
                        help="output folder for midi files")
    parser.add_argument("--num_notes", type=int, default=256,
                        help="number of notes to generate")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="temperature (0.5=conservative, 1.0=normal, 1.5=creative)")
    parser.add_argument("--num_samples", type=int, default=1,
                        help="number of midi files to generate")
    
    args = parser.parse_args()
    
    print(f"project folder: {PROJECT_DIR}")
    print(f"models: {args.model_dir}")
    print(f"output: {args.output_dir}\n")
    
    model_path = find_latest_model(args.model_dir)
    
    if model_path is None:
        exit(1)
    
    generate_and_save(
        model_path=model_path,
        output_dir=args.output_dir,
        num_notes=args.num_notes,
        temperature=args.temperature,
        num_samples=args.num_samples
    )

