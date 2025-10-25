import aio_pika
import json
from typing import List
from fastapi.encoders import jsonable_encoder
from .schemas import EventSchema
from .config import settings


async def publish_to_queue(events: List[EventSchema]):
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("events_queue", durable=True)

        for e in events:
            body = json.dumps(jsonable_encoder(e)).encode()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="events_queue",
            )
