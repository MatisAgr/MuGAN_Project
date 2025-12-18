FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps: fluidsynth and ffmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       fluidsynth \
       ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY back /app/back

# Default SoundFont path (inside image) - can be overridden by env at runtime
ENV SOUNDFONT_PATH=/app/back/utils/FluidR3_GM.sf2

WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "back.main:app", "--host", "0.0.0.0", "--port", "8000"]
