import uuid
import random
import json
from datetime import datetime, timedelta
import time
import requests
from app.config import settings

API_URL = "http://localhost:8000/events"
API_KEY = settings.api_key

NUM_EVENTS = 100_000
BATCH_SIZE = 1000  

event_types = ["login", "logout", "purchase", "view_item", "add_to_cart", "message_sent"]

def generate_event():
    return {
        "event_id": str(uuid.uuid4()),
        "occurred_at": (datetime.utcnow() - timedelta(days=random.randint(0,30))).isoformat(),
        "user_id": f"user_{random.randint(1,10000)}",
        "event_type": random.choice(event_types),
        "properties": {"amount": random.randint(1,100)}
    }

def main():
    start_time = time.time()
    for i in range(0, NUM_EVENTS, BATCH_SIZE):
        batch = [generate_event() for _ in range(BATCH_SIZE)]
        r = requests.post(API_URL, json=batch, headers={"X-API-KEY": API_KEY})
        if r.status_code != 200:
            print("Error:", r.status_code, r.text)
            break
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"Inserted {i + BATCH_SIZE} events...")

    duration = time.time() - start_time
    print(f"Inserted {NUM_EVENTS} events in {duration:.2f}s")
    print(f"Throughput: {NUM_EVENTS/duration:.0f} events/sec")

if __name__ == "__main__":
    main()
