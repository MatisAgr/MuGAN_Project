from pydantic import BaseModel
from typing import Optional


# TODO: à revoir
class GeneratorRequest(BaseModel):
    title: Optional[str] = None
    composer: Optional[str] = None
    duration: int = 30
    temperature: float = 1.0

class GeneratorResponse(BaseModel):
    id: str
    title: str
    url: str
    duration: int
    created: str
