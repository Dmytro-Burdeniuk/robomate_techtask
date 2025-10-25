import uuid
from pydantic import BaseModel
from datetime import datetime


class EventSchema(BaseModel):
    event_id: uuid.UUID
    occurred_at: datetime
    user_id: str
    event_type: str
    properties: dict
