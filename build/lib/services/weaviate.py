import logging
import os
from dotenv import load_dotenv
from weaviate import use_async_with_embedded, use_async_with_weaviate_cloud
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from uuid import uuid5, NAMESPACE_DNS
from weaviate.classes.query import Rerank, MetadataQuery
from weaviate.client import WeaviateAsyncClient
from weaviate.collections.classes.config import Configure
from weaviate.exceptions import WeaviateInvalidInputException


load_dotenv()


logger = logging.getLogger("Weaviate")


WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_GRPC = os.getenv("WEAVIATE_GRPC")
WEAVIATE_KEY = os.getenv("WEAVIATE_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "course_embeddings")
headers = {
    "X-JinaAI-Api-Key": JINA_API_KEY,
}


# weaviate_client = WeaviateAsyncClient(
#     auth_client_secret=Auth.api_key(WEAVIATE_KEY),
#     additional_headers=headers,
#
# )

weaviate_client: WeaviateAsyncClient = use_async_with_weaviate_cloud(
    auth_credentials=Auth.api_key(WEAVIATE_KEY),
    cluster_url=WEAVIATE_URL,
    headers=headers,
)



async def init_weaviate():
    logger.info("Initializing weaviate...")
    await weaviate_client.connect()
    if not await weaviate_client.collections.exists(COLLECTION_NAME):
        # print("Creating collection...")
        await weaviate_client.collections.create(
                name=COLLECTION_NAME,
                reranker_config=Configure.Reranker.jinaai()
            )
        # print("Collection created Successfully.")
    logger.info("Connected to weaviate.")


async def close_weaviate():
    logger.info("Closing weaviate...")
    await weaviate_client.close()
    logger.debug("Weaviate Closed")


def weaviate_id_from_slug(slug: str):
    return uuid5(NAMESPACE_DNS, slug)


def normalize_weaviate_object(obj):
    return {
                "course_details": obj.properties,
                "score": obj.metadata.score,
                # "rerank_score": obj.metadata.rerank_score,
            }


async def upsert_course_embedding(payload: dict):
    collection = weaviate_client.collections.get(COLLECTION_NAME)

    slug = payload.get("slug")
    if not slug:
        raise ValueError("Slug is required for deterministic Weaviate ID")

    try:
        await collection.data.insert(
            uuid=weaviate_id_from_slug(payload.get("slug")),
            properties={
                    "embedding_text": payload["embedding_text"],
                    "course_title":payload["metadata"]["course_title"],
                    "slug": payload["slug"],
                    "hero_features": payload["metadata"]["hero_features"],
                    "pricing":payload["metadata"]["fee"],
                    "skills": payload["metadata"]["skills"],
                    "prerequisites": payload["metadata"]["prerequisites"],
                    "target_audience": payload["metadata"]["target_audience"],
                    "duration": payload["metadata"]["duration"],
                    "category": payload["metadata"]["category"]
            },
                vector=payload.get("embedding"),
            )

        return True
    except WeaviateInvalidInputException:
        return False


async def fetch_weaviate_object(slug: str):
    collection = weaviate_client.collections.get(COLLECTION_NAME)

    result = await collection.query.fetch_objects(
            filters=Filter.by_property("slug").equal(slug),
            limit=1,
        )

    if not result.objects:
        return None

    obj = result.objects[0]
    return {
        "Properties":obj.properties
    }


async def delete_weaviate_object(slug_list: list[str]):
    collection = weaviate_client.collections.get(COLLECTION_NAME)

    if not slug_list:
        return False

    logger.info("Deleting weaviate object...")
    result = await collection.data.delete_many(
                where=Filter.by_property("slug").contains_any(slug_list),
    )

    logger.info(f"Deleted Data :{result.matches}")
    return result.matches>0


async def fetch_similar_courses(query: str, vector: list[float] | list[int]):
    collection = weaviate_client.collections.get(COLLECTION_NAME)

    result = await collection.query.hybrid(
                    query=query,
                    limit=12,
                    alpha=0.6,
                    vector=vector,
                    threshold=0.6,
        return_metadata=MetadataQuery(
                    score=True,
                    last_update_time=False,
                    creation_time=False,
                    certainty=False,
                    explain_score=False,
                    distance=False,
                    is_consistent=False,
                ),
                include_vector=False,
            )

    if not result.objects:
        return []

    normalized_objects = [normalize_weaviate_object(obj) for obj in result.objects]

    return normalized_objects