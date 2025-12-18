<div align="center">
<img width="1919" height="287" alt="image" src="https://github.com/user-attachments/assets/606cb7d0-c9f6-452c-add3-21c7c47312e2" />

</div>


## MuGAN Project — Docker quickstart

Services:
- backend: FastAPI app (uvicorn) — includes FluidSynth + ffmpeg for MIDI→MP3 conversion
- frontend: Vite React app served by nginx (built from `front/`)

Build & run (requires Docker):

1) Build and start both services with Docker Compose

```bash
docker compose build
docker compose up
```

2) Backend will be available at `http://localhost:8000`
   Frontend at `http://localhost:5173`

Notes:
- The backend uses `back/utils/FluidR3_GM.sf2` by default. You can replace it or override `SOUNDFONT_PATH` env var.
- Generated MP3 files are stored in the host folder `back/data` (mounted into the container).
- If you don't want to install FluidSynth/ffmpeg locally, run via Docker.

## Convert MIDI to MP3 (local setup)
- Download FluidR3_GM.sf2 soundfont from [here](https://member.keymusician.com/Member/FluidR3_GM/index.html) and place it in the back/utils/ directory.

- Should install ffmpeg and fluidsynth on your system for the conversion to work.


### Crédit

- ANGER Matis
- BINET Julien
- BOURGES Carl
- OZDEMIR Sedanur
