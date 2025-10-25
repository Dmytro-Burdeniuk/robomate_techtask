import csv
import os
import json
import sys
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from app.db import SessionLocal
from app.models import Event


def import_events(csv_path):
    db = SessionLocal()
    count = 0

    f = open(csv_path, "r")
    reader = csv.DictReader(f)

    for row in reader:
        e = Event()
        e.event_id = uuid.UUID(row["event_id"])
        e.occurred_at = datetime.fromisoformat(row["occurred_at"])
        e.user_id = row["user_id"]
        e.event_type = row["event_type"]
        e.properties = json.loads(row["properties_json"])

        db.merge(e)
        count += 1

    db.commit()
    db.close()
    print("Імпортовано", count, "подій")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    path = sys.argv[1]
    import_events(path)
