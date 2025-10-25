from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .db import Base


class Event(Base):
    __tablename__ = "events"
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String)
    event_type = Column(String)
    properties = Column(JSON)
