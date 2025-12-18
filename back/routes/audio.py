from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

router = APIRouter()

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROJECT_DIR = Path(__file__).parent.parent.parent
GENERATED_DIR = PROJECT_DIR / "data" / "generated"


@router.get("/audio/generated/{filename}")
async def get_generated_audio_file(filename: str):
    print(f"[ROUTE /api/audio/generated/{filename}] GET request")
    
    file_path = GENERATED_DIR / filename
    
    if not file_path.exists():
        print(f"[ROUTE /api/audio/generated/{filename}] File not found")
        raise HTTPException(status_code=404, detail=f"Generated file {filename} not found")
    
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/midi"
    
    print(f"[ROUTE /api/audio/generated/{filename}] Serving file from {file_path}")
    return FileResponse(
        str(file_path),
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    print(f"[ROUTE /api/audio/{filename}] GET request")
    
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"[ROUTE /api/audio/{filename}] File not found")
        raise HTTPException(status_code=404, detail=f"Audio file {filename} not found")
    
    print(f"[ROUTE /api/audio/{filename}] Serving file from {file_path}")
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
