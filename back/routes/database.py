from fastapi import APIRouter, Query
from typing import List, Optional
from models.music_item import MusicItem
from controllers import database_controller
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/database")
def get_music_database(
    filter: Optional[str] = Query(None, description="Filter by type: Train, Test, Validation, Generated, or all"),
    search: Optional[str] = Query(None, description="Search in title, composer, or tags")
):
    print(f"[ROUTE /api/database] GET request - filter: {filter}, search: {search}")
    items = database_controller.get_all_music(filter_type=filter, search=search)
    return JSONResponse(content=[item.model_dump(by_alias=False) for item in items])

@router.get("/database/{music_id}")
def get_music_by_id(music_id: int):
    print(f"[ROUTE /api/database/{music_id}] GET request")
    music = database_controller.get_music_by_id(music_id)
    if not music:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Music with id {music_id} not found")
    return JSONResponse(content=music.model_dump(by_alias=False))
