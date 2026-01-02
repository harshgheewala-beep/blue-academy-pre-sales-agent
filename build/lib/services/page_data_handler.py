import regex as re
import time
from services.mongo_db import fetch_page_data_using_slug
from logging import Logger
from services.redis_service import redis_client
from redis import Redis
import json
from urllib.parse import urlparse


logger = Logger("Cache Logger")


async def get_last_page_segment(url: str)-> str:
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


async def extract_page_info_from_url(page_url: str) -> dict:
    segment = await get_last_page_segment(page_url)
    if re.fullmatch(
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        string=segment
    ):
        return {
            "page_type": "particular_course_page",
            "slug": segment,
        }

    static_pages = {"courses", "about", "contacts"}
    if segment in static_pages:
        return {
            "page_type": segment,
        }

    return {"page_type": "home_page"}


async def resolve_page_data_by_slug(slug: str):
    key = f"page:course:{slug}"

    # print("Cache Hit for page resolve")
    cached = await redis_client.get(key)
    if cached:
        logger.info(
            "Cache hit, returning cached page data"
        )
        # print(cached)
        return json.loads(cached), "cache"

    page_data = await fetch_page_data_using_slug(slug)
    if not page_data:
        return None, None

    await redis_client.set(
        key,
        json.dumps({
            "slug": slug,
            "data": page_data,
            "source": "mongo_db",
            "updated_at": int(time.time()),
        }),
        ex=3600
    )

    return page_data, "db"
