import logging
import os
from dotenv import load_dotenv
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from uuid import uuid5, NAMESPACE_DNS
from weaviate.classes.query import MetadataQuery
from weaviate.client import WeaviateAsyncClient, WeaviateClient
from weaviate.collections.classes.config import Property, DataType
from weaviate.exceptions import WeaviateInvalidInputException
from weaviate import client

load_dotenv()


logger = logging.getLogger("Weaviate")


WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_KEY = os.getenv("WEAVIATE_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "course_embeddings")
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT"))

# weaviate_async_client: WeaviateAsyncClient = weaviate.use_async_with_weaviate_cloud(
#     auth_credentials=Auth.api_key(WEAVIATE_KEY),
#     cluster_url=WEAVIATE_URL,
#     skip_init_checks=False,
# )


weaviate_client: WeaviateClient = weaviate.connect_to_local(
    host=WEAVIATE_HOST,
    port=WEAVIATE_PORT,
    skip_init_checks=True,
)

weaviate_async_client: WeaviateAsyncClient = weaviate.use_async_with_local(
    host=WEAVIATE_HOST,
    port=WEAVIATE_PORT
)


async def init_weaviate():
    logger.info("Initializing weaviate...")
    await weaviate_async_client.connect()
    if not await weaviate_async_client.collections.exists(COLLECTION_NAME):
        await weaviate_async_client.collections.create(
                name=COLLECTION_NAME,
                properties=[

        Property(name="course_title",
                 description='Course Title',
                 data_type=DataType.TEXT,
                 index_filterable=True),

        Property(name="slug",
                 description='Unique Identifier Slug',
                 data_type=DataType.TEXT,
                 index_filterable=True,
                 index_searchable=True),

        Property(name="category",
                 description='Course Category',
                 data_type=DataType.TEXT,index_filterable=True, index_searchable=True),

        Property(name="hero_features",
                 description='Hero Features',
                 data_type=DataType.TEXT,
                 index_filterable=True),

        Property(name="skills",
                 description='Skills Gained',
                 data_type=DataType.TEXT,
                 index_filterable=True),

        Property(name="target_audience",
                 description='Target Audience (Who should take this course)',
                 data_type=DataType.TEXT,
                 index_filterable=True,
                 index_searchable=True),

        Property(name="prerequisites",
                 description='Skills/Knowledge Required',
                 data_type=DataType.TEXT,
                 index_filterable=True,
                 index_searchable=True),

        Property(name="pricing",
                 description='Pricing of Course',
                 data_type=DataType.TEXT,
                 index_filterable=True,
                 index_searchable=True),

        Property(name="duration",
                 description='Duration of Course',
                 data_type=DataType.TEXT),

        Property(
            name="embedding_text",
            description='Text embedding of Course',
            data_type=DataType.TEXT,
            index_filterable=True,
        ),
    ])
    logger.info("Connected to weaviate.")


async def close_weaviate():
    logger.info("Closing weaviate...")
    await weaviate_async_client.close()
    logger.debug("Weaviate Closed")


def weaviate_id_from_slug(slug: str):
    return uuid5(NAMESPACE_DNS, slug)


def normalize_weaviate_object(obj):
    return {
                "course_details": obj.properties,
                "score": obj.metadata.score,
                # "rerank_score": obj.metadata.rerank_score,
            }


async def upsert_course_embedding(payload: dict)-> None:

    collection = weaviate_async_client.collections.get(COLLECTION_NAME)
    collection2 = weaviate_client.collections.get(COLLECTION_NAME)


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
        return

    except WeaviateInvalidInputException:
        logger.exception(f'Upsert failed for slug: {slug}')
        raise


async def fetch_weaviate_object(slug: str):
    collection = weaviate_async_client.collections.get(COLLECTION_NAME)

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


async def delete_weaviate_object(slug_list: list[str]) -> None:
    collection = weaviate_client.collections.get(COLLECTION_NAME)

    if not slug_list:
        return

    logger.info("Deleting weaviate object...")
    try:

        result = await collection.data.delete_many(
                    where=Filter.by_property("slug").contains_any(slug_list),
        )
    except Exception:
        logger.exception("Failed to delete weaviate object.")
        raise

    logger.info(f"Request deletion (slug) :{len(slug_list)}, matched :{result.matches}")


async def fetch_similar_courses(query: str, vector: list[float] | list[int]):
    collection = weaviate_async_client.collections.get(COLLECTION_NAME)

    result = await collection.query.hybrid(
                    query=query,
                    limit=12,
                    alpha=0.6,
                    vector=vector,
        return_properties=[
            'course_title',
            'slug',
            'category',
            'skills',
            'prerequisites',
            'hero_features',
            'target_audience',
            'duration',
            'pricing',
        ],
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