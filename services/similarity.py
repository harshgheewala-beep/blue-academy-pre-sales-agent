import json
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI
from services.data_handler import normalize_query
from services.redis_service import redis_client
from services.weaviate_service import fetch_similar_courses

load_dotenv()


logger = logging.Logger("Redis Logger")


client=OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

async def get_similar_course_chunks(query: str)->list[dict]:
    normalized_query = normalize_query(query)
    res_key = f"weaviate:similarity:{normalized_query}"
    cached = await redis_client.get(res_key)
    if cached:
        logger.info("Cache hit, returning similar courses from redis")
        return json.loads(cached)

    logger.info("Cache miss, returning similar courses from weaviate")

    emb_key = f"emb:{normalized_query}"
    cached = await redis_client.get(emb_key)


    if not cached:
        query_embedding = client.embeddings.create(
            input=query,
            model="text-embedding-3-small",
            encoding_format="float",
        ).data[0].embedding
        await redis_client.set(emb_key, json.dumps(query_embedding), ex=3600)
    else:
        query_embedding = json.loads(cached)

    output = await fetch_similar_courses(query, query_embedding)

    await redis_client.set(
        res_key,
        json.dumps(output),
        ex=1800
    )

    return output


async def get_course_alternatives():
    pass
