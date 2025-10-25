import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from datetime import datetime, timedelta
from app.config import settings

client = TestClient(app)
API_KEY = settings.api_key


def test_ingest_and_stats():
    events = [
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": today,
            "user_id": "user_1",
            "event_type": "login",
            "properties": {"device": "web"},
        },
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": today,
            "user_id": "user_2",
            "event_type": "purchase",
            "properties": {"amount": 50},
        },
    ]

    headers = {"X-API-KEY": API_KEY}
    r = client.post("/events", json=events, headers=headers)
    assert r.status_code == 200
    assert r.json()["inserted"] == 2

    # GET /stats/dau
    today = datetime.utcnow().date().isoformat()
    r = client.get(f"/stats/dau?from={today}&to={today}", headers=headers)

    assert r.status_code == 200
    assert "dau" in r.json()
    assert len(r.json()["dau"]) >= 1
