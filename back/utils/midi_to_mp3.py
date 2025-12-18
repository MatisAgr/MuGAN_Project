"""
MIDI to MP3 converter utility.

Requirements:
    - FluidSynth installed on the system and available in PATH
    - FFmpeg installed on the system and available in PATH
    - A SoundFont (.sf2) available
    - mutagen for audio metadata extraction
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from mutagen.mp3 import MP3


load_dotenv()


DEFAULT_SOUNDFONT = os.getenv("SOUNDFONT_PATH")
FLUIDSYNTH_PATH = os.getenv("FLUIDSYNTH_PATH")
# Définit back/data comme dossier de sortie par défaut
BACK_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_audio_duration(audio_path: str) -> float:
    """
    Extract MP3 duration using mutagen.
    Returns duration in seconds.
    """
    try:
        audio = MP3(audio_path)
        duration = audio.info.length  # durée en secondes
        return duration
    except Exception as e:
        print(f"[MIDI_CONVERTER] Error extracting duration: {e}")
        return 0.0

def midi_to_mp3(
    midi_path: str,
    soundfont_path: str = None,
    output_dir: str = None
) -> tuple:
    """
    Convertit un fichier MIDI en MP3 en utilisant FluidSynth et FFmpeg.
    Retourne un tuple (mp3_path, duration_seconds).
    """
    
    # 1. Validation des entrées
    midi_path = Path(midi_path).expanduser().resolve()
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    sf_path_str = soundfont_path or DEFAULT_SOUNDFONT
    if not sf_path_str:
        raise FileNotFoundError("SoundFont path not provided. Set SOUNDFONT_PATH in .env or pass it.")

    soundfont_path = Path(sf_path_str).expanduser().resolve()
    if not soundfont_path.exists():
        raise FileNotFoundError(f"SoundFont not found: {soundfont_path}")

    # 2. Préparation du dossier de sortie
    if output_dir is None:
        output_dir = BACK_DATA_DIR
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    mp3_filename = midi_path.with_suffix('.mp3').name
    mp3_path = output_dir / mp3_filename

    # Si le MP3 existe déjà, on ne refait pas le travail
    if mp3_path.exists():
        print(f"[MIDI_CONVERTER] MP3 already exists: {mp3_path}")
        duration_seconds = get_audio_duration(str(mp3_path))
        return (str(mp3_path), duration_seconds)

    print(f"[MIDI_CONVERTER] Converting {midi_path.name}...")

    # 3. Processus de conversion avec dossier temporaire sécurisé
    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = Path(temp_dir) / "output.wav"

        # --- Étape A : MIDI -> WAV (FluidSynth) ---
        fluidsynth_exe = FLUIDSYNTH_PATH or shutil.which("fluidsynth")
        if not fluidsynth_exe or not Path(fluidsynth_exe).exists():
            raise RuntimeError(
                f"fluidsynth not found. "
                f"Set FLUIDSYNTH_PATH env variable or add to PATH. "
                f"Expected: C:\\Program Files\\env\\fluidsynth-v2.5.1-win10-x64-cpp11\\bin\\fluidsynth.exe"
            )

        fluidsynth_cmd = [
            fluidsynth_exe,
            "-ni",
            "-F", str(wav_path),
            "-r", "44100",
            str(soundfont_path),
            str(midi_path),
        ]

        try:
            subprocess.run(fluidsynth_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"fluidsynth failed: {e.stderr.strip()}")

        if not wav_path.exists():
            raise RuntimeError("fluidsynth did not produce WAV output")

        # --- Étape B : WAV -> MP3 (FFmpeg) ---
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise RuntimeError("ffmpeg not found in PATH; required for MP3 conversion")

        ff_cmd = [
            ffmpeg_path,
            "-y",
            "-i", str(wav_path),
            "-acodec", "libmp3lame",
            "-b:a", "192k",
            str(mp3_path),
        ]

        try:
            subprocess.run(ff_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg failed: {e.stderr.strip()}")

    # Le dossier temp_dir et le fichier .wav sont supprimés automatiquement ici
    
    if not mp3_path.exists():
        raise RuntimeError("MP3 conversion failed; output file missing")

    # Extraire la durée réelle du fichier MP3 avec ffprobe
    duration_seconds = get_audio_duration(str(mp3_path))

    print(f"[MIDI_CONVERTER] Success: {mp3_path} (duration: {duration_seconds:.2f}s)")
    return (str(mp3_path), duration_seconds)