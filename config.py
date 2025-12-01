import os
from dotenv import load_dotenv
import redis

load_dotenv()

def get_redis_client():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 5000))
    password = os.getenv("REDIS_PASSWORD") or None
    return redis.Redis(host=host, port=port, password=password, decode_responses=True)
