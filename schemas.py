import datetime
from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class DetectionResponse(BaseModel):
    id: int
    task_id: str
    frame_number: int
    confidence: float
    cars_count: int
    image_path: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
