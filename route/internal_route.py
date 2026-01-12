import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import uuid
from services.mongo_db import get_sync_details, update_sync_details, fetch_changes, increment_interest_count
from services.ingestion import ingest_course_embedding
from services.weaviate_service import delete_weaviate_object
from services.data_handler import clean_data_v2
import json
from starlette.responses import JSONResponse
from services.redis_service import redis_client
from logging import Logger


logger = Logger("Internal Route Log")


router = APIRouter(
    prefix="/internal",
    tags=["Internals"],
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


@router.post("/sync_mongo_data",
             description="Synchronize Weaviate Collection with Mongo DB Collection")
async def sync_mongo_data():
    try:
        last_sync_time = await get_sync_details()
        print(f"Last Update timestamp: {last_sync_time}")

        changes = await fetch_changes(last_sync_time)


        if not changes:
            logger.info("No changes found")
            return JSONResponse(
                status_code=200,
                content={
                    "details": "Data is already synced"
                }
            )

        slugs_to_purge = [doc["slug"] for doc in changes]
        updated_data = [doc for doc in changes if not doc["isDeleted"]]

        await delete_weaviate_object(slugs_to_purge)

        if not updated_data:
            return JSONResponse(
                status_code=200,
                content = {
                    "details": "Data Synced Successfully"
                }
            )

        # Uncomment this if v2 does not work
        # cleaned_data = clean_data(updated_data)

        cleaned_data = clean_data_v2(updated_data)

        ingestion_complete = await ingest_course_embedding(cleaned_data)

        if ingestion_complete:
            await update_sync_details()

            return {
                "status": "success",
                "message": "Data synced successful",
            }

        else:
            return {
                "status": "fail",
                "message": "Data synced failed",
            }


    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync data :{str(e)}")



@router.post('/mark_user_interested/{course_slug}')
async def mark_user_interested(course_slug: str):
    try:
        await increment_interest_count(course_slug)
        return True
    except Exception as e:
        return False