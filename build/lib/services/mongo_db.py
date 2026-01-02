import asyncio
import datetime
import os

import bson
from dotenv import load_dotenv
import logging
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from bson.objectid import ObjectId
from datetime import timezone
from bson.timestamp import Timestamp


load_dotenv()


logger = logging.getLogger("Mongo DB")


uri = os.getenv("MONGO_URI")
async_mongo_client = AsyncMongoClient(uri)


def close_mongo_connection():
    logger.info("Closing mongo connection...")
    async_mongo_client.close()
    logger.info("Mongo connection closed")


def normalize_mongo_doc(obj):
    if isinstance(obj, dict):
        return {
            k: normalize_mongo_doc(v)
            for k, v in obj.items()
            if k != "_id"
        }
    elif isinstance(obj, list):
        return [normalize_mongo_doc(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj


async def update_sync_details():
    dbname = async_mongo_client["blue-blue_academy"]
    collection = dbname["update_sync_details"]
    await collection.update_one(
        filter={
            "_id": ObjectId('694259afeec2a03a77624388')
        },
        update={
            "$set":{
                "updated_at":datetime.datetime.now(tz=datetime.timezone.utc),
            }
        }
    )
    logger.info("Update sync details complete")


async def get_sync_details():
    dbname = async_mongo_client["blue-blue_academy"]
    collection = dbname["update_sync_details"]
    sync_details = await collection.find_one()

    return sync_details["updated_at"]



async def fetch_page_data_using_slug(slug: str)-> dict | None:
    dbname = async_mongo_client["blue-blue_academy"]
    collection = dbname["courses"]
    pipeline = [
        {"$match": {"slug": slug}},
        {"$project": {
            "id": {"$toString": "$_id"},
            "_id": 0,
            "slug": 1,
            "title": 1,
            "subtitle": 1,
            "category": 1,
            "duration": 1,
            "fee": 1,
            "skills": 1,
            "prerequisites": 1,
            "targetAudience": 1,
            "curriculum": 1,
            "faqs": 1,
            "heroFeatures": 1
        }
        }
    ]

    cursor = await collection.aggregate(pipeline)
    result = await cursor.to_list()

    # result = await cursor.to_list()
    # result = collection.aggregate(pipeline).to_list()

    cleaned_result = normalize_mongo_doc(result)
    return cleaned_result


async def fetch_changes(last_timestamp: datetime.datetime) -> list[dict]:
    logger.info("Fetching course changes...")

    last_timestamp = last_timestamp.replace(microsecond=0)

    if last_timestamp.tzinfo is None:
        last_timestamp = last_timestamp.replace(tzinfo=datetime.timezone.utc)

    query_time = last_timestamp - datetime.timedelta(milliseconds=1)

    dbname = async_mongo_client["blue-blue_academy"]
    collection = dbname["courses"]


    pipeline = [
        {"$match":{
            "$or":[
                    {"updatedAt": {"$gte": query_time}},
                    {"deletedAt":{"$gte": query_time}},
                ]
            }
        },
        {"$project":{
            "id": {"$toString": "$_id"},
            "_id": 0,
            "slug":1,
            "title":1,
            "subtitle": 1,
            "category":1,
            "duration":1,
            "fee":1,
            "skills":1,
            "prerequisites":1,
            "targetAudience":1,
            "curriculum":1,
            "faqs":1,
            "heroFeatures":1,
            "isDeleted":1
            }
        }
    ]


    cursor = await collection.aggregate(pipeline)
    result = await cursor.to_list()

    cleaned_result = normalize_mongo_doc(result)


    return cleaned_result


async def increment_interest_count(course_slug:str):
    dbname = async_mongo_client["blue-blue_academy"]
    collection = dbname["course_interest"]
    await collection.update_one(
        {"course_slug": course_slug},
        {
            "$inc": {"interest_count": 1},
            "$setOnInsert": {
                "course_slug": course_slug
            }
        },
        upsert=True
    )