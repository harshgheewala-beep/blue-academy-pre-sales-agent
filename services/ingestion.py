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
        payload["course_title"],
        f",Pricing is {payload['fee']},",
        f",Skills Gain : {payload['skills']},",
        f"Category is {payload['category']}",
        payload["hero_features"],
        payload["curriculum"],
        payload["course_description"],
        payload["faqs"],
    ])


def chunk_text(text: str, chunk_size: int = 400):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(text)
    chunks = []

    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i+chunk_size]
        chunks.append(encoding.decode(chunk_tokens))

    return chunks


async def ingest_course_embedding(payload: list[dict]):

    logger.info("Ingesting course embeddings")
    complete_status = False
    for data in payload:
        chunks = await build_chunks(data)
        # full_text = " ".join(data.values())
        # chunks = chunk_text(full_text)

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunks
        ).data[0]

        weaviate_data = {
            "slug": data["slug"],
            "embedding": response.embedding,
            "metadata": data,
            "embedding_text": chunks
        }
        complete_status = await upsert_course_embedding(weaviate_data)

    return complete_status


