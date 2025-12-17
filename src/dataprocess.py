import os, zipfile

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MIDI_DIR = os.path.join(DATA_DIR, "midi")
ZIP_PATH = os.path.join(DATA_DIR, "maestro-v2.0.0.zip")

os.makedirs(MIDI_DIR, exist_ok=True)

with zipfile.ZipFile(ZIP_PATH) as zf:
    for f in zf.namelist():
        if f.endswith('.json'):
            open(os.path.join(DATA_DIR, os.path.basename(f)), "wb").write(zf.read(f))
        elif f.endswith('.mid') or f.endswith('.midi'):
            open(os.path.join(MIDI_DIR, os.path.basename(f)), "wb").write(zf.read(f))

print(f"Done: {len(os.listdir(MIDI_DIR))} midi, {len([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])} json")