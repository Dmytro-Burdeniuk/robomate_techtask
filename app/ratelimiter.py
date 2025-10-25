import time
import redis
from .config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


class RateLimiter:
    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute

    async def allow(self, key: str) -> bool:
        now = int(time.time())
        window_key = f"rate:{key}:{now // 60}"

        current = redis_client.incr(window_key)

        if current == 1:
            redis_client.expire(window_key, 60)

        if current > self.limit:
            return False

        return True


rl = RateLimiter(settings.rate_limit_per_min)
