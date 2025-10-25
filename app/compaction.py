import asyncio
import duckdb
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from app.config import settings

COMPACTION_INTERVAL_HOURS = 24


async def compact_events_to_duckdb():

    pg_engine = create_engine(settings.db_url)
    conn = pg_engine.connect()

    query = """
    SELECT * FROM events
    WHERE occurred_at < NOW() - INTERVAL '7 days';
    """
    df = pd.read_sql(query, conn)

    if df.empty:
        print("No events to compact.")
        conn.close()
        return

    duck_conn = duckdb.connect("/app/data/cold_storage.duckdb")
    duck_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cold_events AS
        SELECT * FROM df LIMIT 0;
    """
    )
    duck_conn.execute("INSERT INTO cold_events SELECT * FROM df;")

    conn.execute("DELETE FROM events WHERE occurred_at < NOW() - INTERVAL '7 days';")

    conn.close()
    duck_conn.close()


async def scheduler():
    while True:
        await compact_events_to_duckdb()
        await asyncio.sleep(COMPACTION_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    asyncio.run(scheduler())
