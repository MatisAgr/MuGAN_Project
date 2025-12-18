import uuid
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.generator_request import GeneratorRequest, GeneratorResponse
from utils.midi_to_mp3 import midi_to_mp3
import database_config

PROJECT_DIR = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_DIR / "src"
GENERATED_DIR = PROJECT_DIR / "data" / "generated"
MODELS_DIR = PROJECT_DIR / "models" / "music_vae"

sys.path.insert(0, str(SRC_DIR))
from generate import find_latest_model, load_model, create_random_seed_sequence, generate_sequence, sequence_to_midi

_model = None
_model_path = None


def get_model():
    """
    Load and cache the model for reuse.
    """
    global _model, _model_path
    
    if _model is None:
        _model_path = find_latest_model(str(MODELS_DIR))
        if _model_path is None:
            raise RuntimeError("No trained model found. Please train a model first.")
        _model = load_model(_model_path)
        if _model is None:
            raise RuntimeError(f"Failed to load model from {_model_path}")
    
    return _model


def save_generated_music_to_db(
    generation_id: str,
    title: str,
    composer: Optional[str],
    midi_filename: str,
    audio_filename: str,
    num_events: int,
    temperature: float,
    duration: int = 0
) -> bool:
    """
    Save generated music metadata to MongoDB.
    Duration is stored in seconds.
    """
    try:
        db = database_config.get_database()
        collection = db.generated_music
        
        doc = {
            "id": generation_id,
            "canonical_title": title,
            "canonical_composer": composer or "AI Generated",
            "year": datetime.now().year,
            "split": "generated",
            "duration": duration,
            "created": datetime.now().isoformat(),
            "plays": 0,
            "tags": ["ai-generated", "piano"],
            "midi_filename": midi_filename,
            "audio_filename": audio_filename,
            "num_events": num_events,
            "temperature": temperature
        }
        
        collection.insert_one(doc)
        print(f"[GENERATOR CONTROLLER] Saved to database: {title}")
        return True
    except Exception as e:
        print(f"[GENERATOR CONTROLLER] Database error: {e}")
        return False


def generate_music(request: GeneratorRequest) -> GeneratorResponse:
    """
    Generate music using the trained model.
    """
    print(f"[GENERATOR CONTROLLER] Received generation request")
    print(f"  - Title: {request.title}")
    print(f"  - Composer: {request.composer}")
    print(f"  - Num Events: {request.num_events}")
    print(f"  - Temperature: {request.temperature}")
    
    generation_id = str(uuid.uuid4())
    
    os.makedirs(GENERATED_DIR, exist_ok=True)
    
    model = get_model()
    
    print(f"[GENERATOR CONTROLLER] Generating music sequence...")
    seed = create_random_seed_sequence(32)
    sequence = generate_sequence(model, seed, request.num_events, request.temperature)
    
    midi_filename = f"{generation_id}.mid"
    midi_path = GENERATED_DIR / midi_filename
    
    print(f"[GENERATOR CONTROLLER] Creating MIDI file...")
    success = sequence_to_midi(sequence, str(midi_path), tempo_bpm=120, instrument_name="Piano")
    
    if not success:
        raise RuntimeError("Failed to create MIDI file")
    
    print(f"[GENERATOR CONTROLLER] Converting to MP3...")
    mp3_path, duration_seconds = midi_to_mp3(str(midi_path), output_dir=str(GENERATED_DIR))
    audio_filename = os.path.basename(mp3_path)
    
    title = request.title if request.title else f"Generated Music {generation_id[:8]}"
    
    save_generated_music_to_db(
        generation_id=generation_id,
        title=title,
        composer=request.composer,
        midi_filename=midi_filename,
        audio_filename=audio_filename,
        num_events=request.num_events,
        temperature=request.temperature,
        duration=int(duration_seconds)
    )
    
    response = GeneratorResponse(
        id=generation_id,
        title=title,
        composer=request.composer,
        audio_url=f"/audio/generated/{audio_filename}",
        midi_url=f"/audio/generated/{midi_filename}",
        num_events=request.num_events,
        temperature=request.temperature,
        duration=int(duration_seconds),
        created=datetime.now().isoformat()
    )
    
    print(f"[GENERATOR CONTROLLER] Generation completed: {response.title}")
    return response
