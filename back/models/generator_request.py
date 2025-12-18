from pydantic import BaseModel
from typing import Optional


class GeneratorRequest(BaseModel):
    title: Optional[str] = None
    composer: Optional[str] = None
    num_events: int = 128
    temperature: float = 0.8

class GeneratorResponse(BaseModel):
    id: str
    title: str
    composer: Optional[str] = None
    audio_url: str
    midi_url: str
    num_events: int
    temperature: float
    duration: int
    created: str
