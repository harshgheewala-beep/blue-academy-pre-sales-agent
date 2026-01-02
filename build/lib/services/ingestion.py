from supabase.client import Client
from openai import OpenAI
import os
import tiktoken
from uuid import UUID
from dotenv import load_dotenv
import logging
from services.weaviate import upsert_course_embedding


load_dotenv()


logger = logging.getLogger("Ingestion Service")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


async def build_chunks(payload: dict)-> str:
    return " ".join([
        payload["course_title"],
        f",Pricing is {payload["fee"]},",
        f",Skills Gain : {payload["skills"]},",
        f"Category is {payload["category"]}",
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

def ingest_course_chunks(course_id: str | UUID, db: Client, is_updated = False):

    course = (
        db.table("course_details")
        .select("*")
        .eq("course_id", course_id)
        .single()
        .execute()
    ).data

    full_text = (
        (course.get("full_description") or "") + "\n" +
        (course.get("curriculum") or "") + "\n" +
        (course.get("faq") or "")
    )

    chunks = chunk_text(full_text)

    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    ).data

    row = []
    for idx, (chunk,emb) in enumerate(zip(chunks,embedding)):
        row.append({
            "course_id": course_id,
            "chunk_index": idx + 1,
            "content": chunk,
            "embedding": emb.embedding,
        })

    db.table("course_chunks").insert(
        json=row,
        upsert=is_updated).execute()

    print(f"Generated {len(chunks)} chunks for course {course_id}")


def ingest_lesson_chunks(payload: dict, db: Client):

    video_title = payload.get("video_title") or ""
    video_transcription = payload.get("video_transcription") or ""

    textual_content = "\n\n".join(filter(None,[
            payload.get("module_name"),
            payload.get("lesson_name"),
            payload.get("lesson_content"),
            video_title,
            video_transcription]
            ))


    chunks = chunk_text(textual_content)

    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    ).data

    rows = []
    for idx, (chunk,emb) in enumerate(zip(chunks,embedding)):
        rows.append({
            "course_id": payload["course_id"],
            "lesson_id": payload["lesson_id"],
            "chunk_text": chunk,
            "embedding": emb.embedding,
            "token_length": len(chunk.split()),  # approx, acceptable
            "order_index": idx + 1
        }
    )

    db.table("lesson_chunks").insert(rows).execute()

    print(f"Generated {len(chunks)} chunks for lesson {payload['lesson_id']}")


async def reingest_lesson(payload: dict, db: Client):
    db.table("lesson_chunks").delete().eq("lesson_id", payload.get("lesson_id")).execute()
    ingest_lesson_chunks(payload, db)


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


