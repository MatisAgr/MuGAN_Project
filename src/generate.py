import os
import argparse
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras

from music21 import stream, instrument, note, chord, tempo, meter
PROJECT_DIR = Path(__file__).parent.parent
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"
GENERATED_DIR = PROJECT_DIR / "generated"

MAX_PITCHES = 4
VOCAB_SIZE = 130
NUM_DURATION_CLASSES = 8
NUM_TIME_SHIFT_CLASSES = 16

DURATION_MAP = {0: 0.125, 1: 0.25, 2: 0.5, 3: 1.0, 4: 2.0, 5: 4.0, 6: 8.0, 7: 16.0}
TIME_SHIFT_MAP = {0: 0.0, 1: 0.125, 2: 0.25, 3: 0.5, 4: 1.0, 5: 2.0, 6: 4.0, 7: 8.0, 
                  8: 16.0, 9: 0.0625, 10: 0.0625, 11: 0.0625, 12: 0.0625, 13: 0.0625, 14: 0.0625, 15: 0.0625}


def find_latest_model(model_dir: str = None) -> str:
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


def create_random_seed_sequence(model: keras.Model,
                                sequence_length: int = 32,
                                temperature: float = 0.8) -> np.ndarray:
    seed = []
    
    for i in range(sequence_length):
        pitch = np.random.randint(50, 90)
        pitch_2 = 128 if np.random.rand() > 0.3 else np.random.randint(50, 90)
        pitch_3 = 128 if np.random.rand() > 0.1 else np.random.randint(50, 90)
        pitch_4 = 128
        
        duration = np.random.randint(0, 8)
        time_shift = np.random.randint(0, 8)
        
        event = [pitch, pitch_2, pitch_3, pitch_4, duration, time_shift]
        seed.append(event)
    
    return np.array(seed, dtype=np.int32)


def generate_and_save(model_path: str,
                      output_dir: str = "../generated",
                      num_events: int = 256,
                      temperature: float = 0.8,
                      num_samples: int = 1):
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
        
        seed = create_random_seed_sequence(model, 32, temperature)
        
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
    parser.add_argument("--model_dir", type=str, default=str(MODELS_DIR))
    parser.add_argument("--output_dir", type=str, default=str(GENERATED_DIR))
    parser.add_argument("--num_events", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--num_samples", type=int, default=1)
    
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
