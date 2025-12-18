import os
import argparse
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras

from music21 import stream, instrument, note, chord, tempo, meter
from config import MAX_PITCHES, VOCAB_SIZE, NUM_DURATION_CLASSES, NUM_TIME_SHIFT_CLASSES, DURATION_MAP, TIME_SHIFT_MAP

PROJECT_DIR = Path(__file__).parent.parent
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"
GENERATED_DIR = PROJECT_DIR / "generated"


def find_latest_model(model_dir: str = None) -> str:
    """
    Find the latest trained model in the models directory.
    
    Searches for best_model.h5 first (checkpoint with best validation loss),
    then falls back to model_final.h5 (final trained model).
    
    Args:
        model_dir: Directory containing models. Defaults to MODELS_DIR if None.
        
    Returns:
        Path to the model file, or None if no model found.
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
    return None


def load_model(model_path: str) -> keras.Model:
    """
    Load a trained Keras model from disk.
    
    Args:
        model_path: Path to the .h5 model file.
        
    Returns:
        Loaded Keras model, or None if loading failed.
    """
    try:
        model = keras.models.load_model(model_path)
        print(f"model loaded: {model_path}")
        return model
    except Exception as e:
        print(f"error loading model: {e}")
        return None


def sample_with_temperature(predictions, temperature):
    predictions = np.log(predictions + 1e-10) / temperature
    predictions = np.exp(predictions) / np.sum(np.exp(predictions))
    return np.random.choice(len(predictions), p=predictions)


def generate_sequence(model: keras.Model,
                      seed_sequence: np.ndarray,
                      length: int = 128,
                      temperature: float = 0.8) -> list:
    """
    Generate a sequence of music events using the trained model.
    
    Takes a seed sequence and generates additional events by:
    1. Feeding the last 31 events to the model
    2. Sampling predictions for each output head using temperature
    3. Repeating until target length is reached
    
    The model outputs 6 values per event:
    - pitch_0, pitch_1, pitch_2, pitch_3: polyphonic pitches (0-129, where 129 = rest)
    - duration: duration class (0-7)
    - time_shift: time shift class (0-8)
    
    Args:
        model: Trained Keras model with 6 output heads.
        seed_sequence: Initial sequence of shape (sequence_length, 6).
        length: Total target length of generated sequence.
        temperature: Sampling temperature (higher = more random, lower = more deterministic).
        
    Returns:
        List of events, each event is a list of 6 integers.
    """
    generated = [list(event) for event in seed_sequence]
    
    print(f"\ngeneration of {length} events (temperature={temperature})...")
    
    for i in range(length - len(seed_sequence)):
        input_seq = np.array([generated[-31:]], dtype=np.float32)
        
        predictions = model.predict(input_seq, verbose=0)
        
        event = []
        for j in range(MAX_PITCHES):
            pitch = sample_with_temperature(predictions[j][0], temperature)
            pitch = np.clip(int(pitch), 0, 129)
            event.append(pitch)
        
        duration = sample_with_temperature(predictions[MAX_PITCHES][0], temperature)
        duration = np.clip(int(duration), 0, NUM_DURATION_CLASSES - 1)
        time_shift = sample_with_temperature(predictions[MAX_PITCHES + 1][0], temperature)
        time_shift = np.clip(int(time_shift), 0, NUM_TIME_SHIFT_CLASSES - 1)
        
        event.append(int(duration))
        event.append(int(time_shift))
        
        generated.append(event)
        
        if (i + 1) % 32 == 0:
            print(f"  {i + 1} / {length - len(seed_sequence)} events generated")
    
    return generated


def sequence_to_midi(events_sequence: list,
                     output_path: str,
                     tempo_bpm: int = 120,
                     instrument_name: str = "Piano") -> bool:
    """
    Convert a sequence of music events to a MIDI file.
    
    Event format: [pitch_0, pitch_1, pitch_2, pitch_3, duration_class, time_shift_class]
    
    Rules:
    - Pitches in range [0, 127] are valid note pitches
    - Pitch value 129 represents a rest event (all pitches = 129)
    - Pitch value 128 represents no pitch (ignored in chord building)
    - Multiple valid pitches create a chord
    - Time shift is applied before placing the note/chord/rest
    - Events with all pitches as 128 or 129 are skipped silently (padding)
    
    Args:
        events_sequence: List of events, each with 6 values.
        output_path: Path where MIDI file will be saved.
        tempo_bpm: Tempo in beats per minute.
        instrument_name: Instrument type (Piano, Violin, etc).
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        score = stream.Score()
        part = stream.Part()
        
        if instrument_name.lower() == "piano":
            part.append(instrument.Piano())
        elif instrument_name.lower() == "violin":
            part.append(instrument.Violin())
        else:
            part.append(instrument.Piano())
        
        part.append(tempo.MetronomeMark(number=tempo_bpm))
        part.append(meter.TimeSignature('4/4'))
        
        current_offset = 0.0
        
        for event in events_sequence:
            pitches = event[:MAX_PITCHES]
            duration_class = int(event[MAX_PITCHES])
            time_shift_class = int(event[MAX_PITCHES + 1])
            
            time_shift = TIME_SHIFT_MAP.get(time_shift_class, 0.0)
            current_offset += time_shift
            
            duration = DURATION_MAP.get(duration_class, 0.5)
            
            valid_pitches = [int(p) for p in pitches if 0 <= int(p) <= 127]
            
            if len(valid_pitches) == 0:
                if int(pitches[0]) == 129:
                    r = note.Rest(quarterLength=duration)
                    r.offset = current_offset
                    part.append(r)
                # Else: all pitches are padding (128), skip silently
            elif len(valid_pitches) == 1:
                n = note.Note(valid_pitches[0], quarterLength=duration)
                n.offset = current_offset
                part.append(n)
            else:
                c = chord.Chord(valid_pitches, quarterLength=duration)
                c.offset = current_offset
                part.append(c)
        
        score.append(part)
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        score.write('midi', fp=output_path)
        
        print(f"midi generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"error creating midi: {e}")
        return False


def create_random_seed_sequence(sequence_length: int = 32) -> np.ndarray:
    """
    Create a random seed sequence for generation.
    
    Generates random events with pitches in the middle range (50-90)
    and random duration/time_shift classes to start generation.
    
    Args:
        sequence_length: Number of events to generate for seed.
        
    Returns:
        Array of shape (sequence_length, 6) with random events.
    """
    seed = []
    
    for i in range(sequence_length):
        pitch = np.random.randint(50, 90)
        pitch_2 = 128 if np.random.rand() > 0.3 else np.random.randint(50, 90)
        pitch_3 = 128 if np.random.rand() > 0.1 else np.random.randint(50, 90)
        pitch_4 = 128 if np.random.rand() > 0.05 else np.random.randint(50, 90)
        
        duration = np.random.randint(0, NUM_DURATION_CLASSES)
        time_shift = np.random.randint(0, NUM_TIME_SHIFT_CLASSES)
        
        event = [pitch, pitch_2, pitch_3, pitch_4, duration, time_shift]
        seed.append(event)
    
    return np.array(seed, dtype=np.int32)


def generate_and_save(model_path: str,
                      output_dir: str = "../generated",
                      num_events: int = 256,
                      temperature: float = 0.8,
                      num_samples: int = 1):
    """
    Generate MIDI files using the trained model.
    
    Loads model, generates specified number of sequences, converts to MIDI.
    
    Args:
        model_path: Path to trained model file.
        output_dir: Directory to save MIDI files.
        num_events: Number of events to generate per sequence.
        temperature: Sampling temperature for generation.
        num_samples: Number of MIDI files to generate.
    """
    model = load_model(model_path)
    if model is None:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"music generation")
    print(f"{'='*60}")
    print(f"configuration:")
    print(f"   - model: {model_path}")
    print(f"   - number of events: {num_events}")
    print(f"   - temperature: {temperature}")
    print(f"   - files to generate: {num_samples}")
    
    for i in range(num_samples):
        print(f"\n[{i+1}/{num_samples}] generation of file {i+1}...")
        
        seed = create_random_seed_sequence(32)
        
        sequence = generate_sequence(model, seed, num_events, temperature)
        
        output_filename = f"generated_music_{i+1:03d}.midi"
        output_path = os.path.join(output_dir, output_filename)
        
        success = sequence_to_midi(sequence, output_path, tempo_bpm=120, instrument_name="Piano")
        
        if success:
            print(f"file {i+1} generated")
    
    print(f"\n{'='*60}")
    print(f"files saved in: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="music generation with trained model")
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR), 
                        help="directory containing trained models (default: models/music_vae)")
    parser.add_argument("--output_dir", type=str, default=str(GENERATED_DIR),
                        help="directory to save generated MIDI files (default: generated/)")
    parser.add_argument("--num_events", type=int, default=256,
                        help="number of events to generate per MIDI file (default: 256)")
    parser.add_argument("--temperature", type=float, default=0.8,
                        help="sampling temperature: higher = more random, lower = more deterministic (default: 0.8)")
    parser.add_argument("--num_samples", type=int, default=1,
                        help="number of MIDI files to generate (default: 1)")
    
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
        num_events=args.num_events,
        temperature=args.temperature,
        num_samples=args.num_samples
    )
