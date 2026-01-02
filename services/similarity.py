import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from supabase.client import Client
from openai import OpenAI

from services.data_handler import normalize_query
from services.redis_service import redis_client
from services.weaviate import fetch_similar_courses

load_dotenv()


logger = logging.Logger("Redis Logger")


client=OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


def get_similar_courses(query: str, db: Client, top_k: int = 5):
    query_embedding = client.embeddings.create(
        input=query,
        model="text-embedding-3-small",
        encoding_format="float",
    ).data[0].embedding

    response = db.rpc(
        "match_course_chunks",
        {
            "query_embedding":query_embedding,
            "match_threshold":0,
            "match_count":top_k,
        }
    ).execute()
    #
    # print(response)

    # if response.error:
    #     raise Exception(response.error)

    return response.data



def get_similar_lesson_chunks(query: str, db: Client, top_k: int = 5, filter_course_ids: Optional[list] = None):
    query_embedding = client.embeddings.create(
        input=query,
        model="text-embedding-3-small",
        encoding_format="float",
    ).data[0].embedding

    print(query_embedding)
    response = db.rpc(
        "match_lesson_chunks",
        {
            "query_embedding":query_embedding,
            "match_threshold":0,
            "match_count":top_k,
            "filter_course_ids":filter_course_ids,
        }
    ).execute()

    return response.data





async def get_similar_course_chunks(query: str)->list[dict]:
    normalized_query = normalize_query(query)
    print(normalized_query)
    res_key = f"weaviate:similarity:{normalized_query}"
    cached = await redis_client.get(res_key)
    if cached:
        logger.info("Cache hit, returning similar courses from redis")
        return json.loads(cached)

    logger.info("Cache miss, returning similar courses from weaviate")

    emb_key = f"emb:{normalized_query}"
    query_embedding = await redis_client.get(emb_key)

    if not query_embedding:
        query_embedding = client.embeddings.create(
            input=query,
            model="text-embedding-3-small",
            encoding_format="float",
        ).data[0].embedding
        await redis_client.set(emb_key, json.dumps(query_embedding), ex=3600)


    output = await fetch_similar_courses(query, query_embedding)

    await redis_client.set(
        res_key,
        json.dumps(output),
        ex=1800
    )

    return output



async def get_course_alternatives():
    pass
