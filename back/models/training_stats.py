from pydantic import BaseModel

class TrainingStats(BaseModel):
    epoch: int
    total_epochs: int
    loss: float
    accuracy: float
    val_loss: float
    val_accuracy: float
    learning_rate: float
    batch_size: int
    time_elapsed: float
    eta: float
    stopping: bool = False
