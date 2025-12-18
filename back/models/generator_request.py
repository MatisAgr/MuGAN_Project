from pydantic import BaseModel
from typing import Optional

class GeneratorRequest(BaseModel):
    prompt: Optional[str] = None
    duration: int = 30
    temperature: float = 1.0

class GeneratorResponse(BaseModel):
    id: str
    title: str
    url: str
    duration: int
    created: str
