from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

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
