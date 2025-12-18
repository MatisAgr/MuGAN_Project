"""
MIDI to MP3 converter utility (using midi2audio).

Requirements:
    FluidSynth installed on the system and available in PATH
    A SoundFont (.sf2) available; set path via `SOUNDFONT_PATH` env var or pass it.
"""

import os
import shutil
import subprocess
import tempfile

from dotenv import load_dotenv
from pathlib import Path
from midi2audio import FluidSynth


load_dotenv()
# Default soundfont; can be overridden with SOUNDFONT_PATH env var
DEFAULT_SOUNDFONT = os.getenv("SOUNDFONT_PATH")

# Default backend data directory: back/data (module lives in back/utils so go up one level)
BACK_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def midi_to_mp3(
    midi_path: str,
    soundfont_path: str = None,
    output_dir: str = None
) -> str:
    """
    Convert a MIDI file to MP3 and store it in `output_dir` (defaults to `back/data`).

    Args:
        midi_path: Path to the input MIDI file.
        soundfont_path: Optional path to a .sf2 SoundFont. If None, uses `SOUNDFONT_PATH`.
        output_dir: Optional output directory. If None, uses `back/data`.

    Returns:
        Absolute path to the generated MP3 file.

    Raises:
        FileNotFoundError: If the MIDI file or SoundFont is missing.
        Exception: If conversion fails (propagated from midi2audio/FluidSynth).
    """
    midi_path = Path(midi_path).expanduser().resolve()
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    sf_path_str = soundfont_path or DEFAULT_SOUNDFONT
    if not sf_path_str:
        raise FileNotFoundError("SoundFont path not provided. Set SOUNDFONT_PATH env var or pass it to the function.")

    soundfont_path = Path(sf_path_str).expanduser().resolve()
    if not soundfont_path.exists():
        raise FileNotFoundError(f"SoundFont not found: {soundfont_path}")

    if output_dir is None:
        output_dir = BACK_DATA_DIR
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    mp3_filename = midi_path.with_suffix('.mp3').name
    mp3_path = output_dir / mp3_filename
    # If MP3 already exists, skip conversion and return existing file
    if mp3_path.exists():
        print(f"[MIDI_CONVERTER] MP3 already exists, skipping conversion: {mp3_path}")
        return str(mp3_path)

    print(f"[MIDI_CONVERTER] Converting {midi_path} -> {mp3_path} using {soundfont_path}")


    wav_path = Path(tempfile.mktemp(suffix='.wav'))

    # fluidsynth expects options before positional args; put -F and -r before soundfont and midi
    fluidsynth_cmd = [
        "fluidsynth",
        "-ni",
        "-F",
        str(wav_path),
        "-r",
        "44100",
        str(soundfont_path),
        str(midi_path),
    ]

    try:
        proc = subprocess.run(fluidsynth_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        # Show stderr for debugging
        raise RuntimeError(f"fluidsynth failed: {e.stderr.strip()}")

    if not wav_path.exists():
        raise RuntimeError("fluidsynth did not produce WAV output")

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        wav_path.unlink(missing_ok=True)
        raise RuntimeError("ffmpeg not found in PATH; required to convert WAV to MP3")

    ff_cmd = [
        ffmpeg_path,
        "-y",
        "-i",
        str(wav_path),
        "-acodec",
        "libmp3lame",
        "-b:a",
        "192k",
        str(mp3_path),
    ]

    try:
        subprocess.run(ff_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.strip()}")
    finally:
        try:
            wav_path.unlink()
        except Exception:
            pass

    if not mp3_path.exists():
        raise RuntimeError("MP3 conversion failed; output file missing")

    print(f"[MIDI_CONVERTER] Created: {mp3_path}")
    return str(mp3_path)
