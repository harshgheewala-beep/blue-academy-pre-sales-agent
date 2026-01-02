import time

from fastapi import APIRouter
import json
from starlette.responses import JSONResponse

from services.redis_service import redis_client
from logging import Logger


logger = Logger("Internal Route Log")


router = APIRouter(
    prefix="/internal",
    tags=["Page"],
)


@router.post(
"/cache/page",
    description="Preload Page Data in Cache"
)
async def prewarn_page_cache(payload: dict):
    slug = str(payload["slug"])
    data = payload["data"]
    source = str(payload.get("source","api_call"))

    key = f"page:course:{slug}"

    logger.info("Storing Page in Cache...")
    await redis_client.set(
                key,
                json.dumps({
                    "slug": slug,
                    "data":data,
                    "source":source,
                    "updated_at": int(time.time()),
                }),
            ex=3600
        )

    logger.info("Cache stored")

    return JSONResponse(status_code=200,
                        content={"details":
                                 "OK"})
