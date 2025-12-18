from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TrainingEpoch(BaseModel):
    epoch: int
    loss: float
    accuracy: float
    val_loss: float
    val_accuracy: float
    learning_rate: float
    batch_size: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TrainingSession(BaseModel):
    session_id: Optional[str] = None
    total_epochs: int
    current_epoch: int = 0
    status: str = "running"
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    elapsed_time: float = 0
    epochs_data: List[TrainingEpoch] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TrainingSessionResponse(BaseModel):
    session_id: str
    total_epochs: int
    current_epoch: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    elapsed_time: float
    epochs_data: List[TrainingEpoch]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
