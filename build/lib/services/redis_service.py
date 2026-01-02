import asyncio
import os
import json, time
from redis.asyncio.client import Redis
from redis.cache import CacheConfig
from dotenv import load_dotenv
import logging


load_dotenv()


logger = logging.getLogger("Redis")


REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_USERNAME = os.getenv('REDIS_USERNAME', 'default')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
DECODE_RESPONSE = os.getenv('DECODE_RESPONSE', True)


redis_client  = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    username=REDIS_USERNAME,
    decode_responses=DECODE_RESPONSE,
    protocol=3
)


async def disconnect_redis():
    logger.info(f"Disconnecting Redis Client...")
    await redis_client.aclose()
    logger.info(f"Redis Client Disconnected")


NAV_TTL = 1800  # 30 minutes

async def update_session_navigation(
    session_id: str,
    url: str,
    slug: str
):
    key = f"session:{session_id}:nav"

    payload = {
        "last_url": url,
        "slug": slug,
        "updated_at": int(time.time())
    }

    await redis_client.set(key, json.dumps(payload), ex=NAV_TTL)