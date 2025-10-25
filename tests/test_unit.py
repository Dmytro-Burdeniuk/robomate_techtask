import uuid
from datetime import datetime
from app.db import SessionLocal
from app.models import Event

def test_idempotency():
    db = SessionLocal()

    event_id = uuid.uuid4()
    e1 = Event(
        event_id=event_id,
        occurred_at=datetime.utcnow(),
        user_id="user_1",
        event_type="login",
        properties={"device": "web"}
    )

    db.merge(e1)
    db.commit()

    
    e2 = Event(
        event_id=event_id,
        occurred_at=datetime.utcnow(),
        user_id="user_1",
        event_type="login",
        properties={"device": "web"}
    )
    db.merge(e2)
    db.commit()

    
    count = db.query(Event).filter(Event.event_id == event_id).count()
    assert count == 1

    db.close()
