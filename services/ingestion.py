import asyncio

from openai import OpenAI
import os
import tiktoken
from uuid import UUID
from dotenv import load_dotenv
import logging
from services.weaviate_service import upsert_course_embedding


load_dotenv()


logger = logging.getLogger("Ingestion Service")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


async def build_chunks(payload: dict)-> str:
    return " ".join([
        payload['course_title'],
        payload['subtitle'],
        f",Pricing is {payload['fee']},",
        f",Skills Gain : {payload['skills']},",
        f"Category is {payload['category']}",
        f"Course Outcome is {payload['outcomes']},",
        f"Hero Features : {payload['hero_features']}",
        payload['curriculum'],
        payload['course_description'],
        payload['faqs'],
    ])


def chunk_text(text: str, chunk_size: int = 400):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(text)
    chunks = []

    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i+chunk_size]
        chunks.append(encoding.decode(chunk_tokens))

    return chunks


async def ingest_course_embedding(payload: list[dict])-> None:

    if not payload:
        logger.info('No Document to Ingest')
        return

    logger.info(f"Ingesting {len(payload)} course embeddings")

    for data in payload:
        text = await build_chunks(data)
        # full_text = " ".join(data.values())
        # chunks = chunk_text(full_text)
        try:
            response = await asyncio.to_thread(
                    client.embeddings.create,
                    model="text-embedding-3-small",
                    input=text
                )

            weaviate_data = {
                "slug": data["slug"],
                "embedding": response.data[0].embedding,
                "metadata": data,
                "embedding_text": text
            }

            await upsert_course_embedding(weaviate_data)
            logger.info(f"Ingested {data['slug']}")

        except Exception:
            logger.exception(f'Error occurred during ingestion')
            raise

    logger.info(f'New courses Ingested')
    return





