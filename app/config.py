import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    db_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL")
    api_key = os.getenv("API_KEY")
    rate_limit_per_min = int(os.getenv("RATE_LIMIT"))
    rabbitmq_url = os.getenv("RABBITMQ_URL")

settings = Settings()