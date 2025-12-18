from fastapi import APIRouter
from ..models.generator_request import GeneratorRequest, GeneratorResponse
from ..controllers import generator_controller

router = APIRouter()

@router.post("/generator", response_model=GeneratorResponse)
async def generate_music(request: GeneratorRequest):
    print(f"[ROUTE /api/generator] POST request")
    return generator_controller.generate_music(request)
