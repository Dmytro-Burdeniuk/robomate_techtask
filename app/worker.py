import asyncio
import aio_pika
import json
from datetime import datetime
import uuid
from .db import SessionLocal
from .models import Event
from .config import settings

RETRY_LIMIT = 3  
DLQ_NAME = "events_dlq"


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process(ignore_processed=True):
        try:
            data = json.loads(message.body)

            db = SessionLocal()
            event = Event(
                event_id=uuid.UUID(data["event_id"]),
                occurred_at=datetime.fromisoformat(data["occurred_at"]),
                user_id=data["user_id"],
                event_type=data["event_type"],
                properties=data["properties"],
            )
            db.merge(event)
            db.commit()
            db.close()

        except Exception as e:
            headers = message.headers or {}
            retries = headers.get("x-retries", 0)

            if retries < RETRY_LIMIT:
                await message.nack(requeue=False)

                channel = await message.channel.get_channel()
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        headers={"x-retries": retries + 1},
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key="events_queue",
                )
            else:
                channel = await message.channel.get_channel()
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        headers={"x-original-error": str(e)},
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=DLQ_NAME,
                )


async def main():
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()

        
        await channel.declare_exchange("events_exchange", aio_pika.ExchangeType.DIRECT)
        await channel.declare_exchange("dlx_exchange", aio_pika.ExchangeType.DIRECT)

        await channel.declare_queue(
            "events_queue",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "dlx_exchange",
                "x-dead-letter-routing-key": DLQ_NAME,
            },
        )

        await channel.declare_queue(DLQ_NAME, durable=True)
        await channel.default_exchange.bind("events_queue", "events_queue")

        await channel.set_qos(prefetch_count=10)

        queue = await channel.get_queue("events_queue")
        await queue.consume(process_message)
        print("Worker started")

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
