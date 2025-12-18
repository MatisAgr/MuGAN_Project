from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union
import hashlib

class MusicItem(BaseModel):
    id: Optional[Union[int, str]] = None
    title: Optional[str] = Field(None, alias='canonical_title')
    composer: Optional[str] = Field(None, alias='canonical_composer')
    year: Optional[int] = None
    type: Literal['Train', 'Test', 'Validation', 'Generated'] = Field('Train', alias='split')
    duration: Optional[int] = None
    created: Optional[str] = None
    plays: int = 0
    tags: List[str] = Field(default_factory=list)
    midi_filename: Optional[str] = None
    audio_filename: Optional[str] = None

    model_config = {
        'populate_by_name': True,
        'use_enum_values': True
    }

    @field_validator('duration', mode='before')
    @classmethod
    def convert_duration(cls, v):
        if isinstance(v, float):
            return int(v)
        return v

    @field_validator('type', mode='before')
    @classmethod
    def capitalize_type(cls, v):
        if isinstance(v, str):
            lower_v = v.lower()
            if lower_v == 'generated':
                return 'Generated'
            return v.capitalize()
        return v

    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v, values):
        if v is None:
            title = values.data.get('canonical_title', '') or ''
            composer = values.data.get('canonical_composer', '') or ''
            hash_input = f"{title}{composer}".encode()
            hash_obj = hashlib.md5(hash_input)
            return int(hash_obj.hexdigest(), 16) % (2**31)
        # Accept both int and string (UUID for generated music)
        return v
