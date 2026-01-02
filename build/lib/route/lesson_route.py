from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from supabase.client import Client

from services import similarity
from services.ingestion import reingest_lesson
from services.supabase_service import get_supabase_client
from storage3.types import FileOptions
from services.video_transcription import video_transcription_pipeline

router = APIRouter(
    tags=["Lessons"],
    prefix="/lessons",
)



@router.get("/{lesson_id}",
            description="Get a lesson's details")
async def get_lesson(lesson_id: str, db: Client = Depends(get_supabase_client)):
    response = db.table("lessons").select("*").eq("id", lesson_id).single().execute()
    return response.data


@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: str, db: Client = Depends(get_supabase_client)):
    db.table("lesson_videos").delete().eq("lesson_id", lesson_id).execute()

    res = db.table("lessons").delete().eq("id", lesson_id).execute()
    return {"deleted": res.data}



@router.post("/{lesson_id}/video/upload",
             description="Create a new lesson video")
async def upload_lesson_video(lesson_id: str,video_title:str = None, video: UploadFile = File(...), db: Client = Depends(get_supabase_client)):

    print(f"Lesson id: {lesson_id}")
    print(f"Video: {video}")

    if not video_title:
        video_title = video.filename.split(".")[0]

    lesson = (db.table("lessons").
              select(
                "id,"
                "module_id,"
                "modules(course_id)")
              .eq("id", lesson_id).execute())


    if not lesson.data:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course_id = lesson.data[0]["modules"]["course_id"]
    module_id = lesson.data[0]["module_id"]

    if video.content_type not in ["video/mp4", "video/mkv", "video/mov"]:
        raise HTTPException(status_code=400, detail="Unsupported video format")


    new_video = (db.table("lesson_videos")
                 .insert({
                    "lesson_id": lesson_id,
                    "title": video_title,
                    "video_url": None,
                    "transcription_mode": "No"
    }).execute())


    if not new_video.data:
        raise HTTPException(status_code=500, detail="Database insert failed")


    video_id = new_video.data[0]["id"]
    file_ext = video.filename.split(".")[-1]
    file_path = f"{course_id}/{module_id}/{lesson_id}/{video_id}.{file_ext}"
    file_bytes = video.file.read()

    options: FileOptions = {
        "content-type": "video/mp4",
        "cache-control": "3600",
        "upsert": "false",
    }

    db.storage.from_("videos").upload(
        path=file_path,
        file=file_bytes,
        file_options=options
    )

    video_url = db.storage.from_("videos").get_public_url(path=file_path)
    print(video_url)

    db.table("lesson_videos").update(
        {"video_url":video_url}
    ).eq("id",video_id).execute()


    suffix = "." +video.filename.split(".")[-1]
    # audio_bytes = await extract_audio_from_video(video_bytes=file_bytes,suffix=suffix)

    try:
        transcript = await video_transcription_pipeline(video_bytes=file_bytes, suffix=suffix)

        print(transcript)
        db.table("lesson_videos").update({
            "transcription_mode":"Auto",
        })

        response = db.table("video_transcription").insert(
            {
                "video_id":video_id,
                "transcription":transcript
             }
        ).execute()



        if not response.data:
            raise HTTPException(status_code=500, detail=f"Failed to store transcription. Video saved video with id {video_id}")

        # transcription_id = response.data[0]["id"]

        payload = await get_all_textual_data(lesson_id, db)

        import threading
        threading.Thread(
            target=reingest_lesson,
            args=(payload, db),
            daemon=True
        ).start()

        return {"detail": "Video uploaded & lesson reindexed"}


        return {
            "transcription": transcript,
            "transcription_mode": "Auto",
            "status_code":200
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lesson_id}/get_all_textual_data",
            description="Get all textual data")
async def get_all_textual_data(lesson_id: str, db: Client = Depends(get_supabase_client)):
    lesson_resp = db.table("lessons").select(
        "id, name, lesson_content, modules(name, course_id)"
    ).eq("id", lesson_id).single().execute()

    if not lesson_resp.data:
        raise HTTPException(status_code=404,
                            detail="Lesson not found")

    lesson = lesson_resp.data

    transcription_resp = db.table("video_transcription").select(
        "transcription, lesson_videos(title)"
    ).eq("lesson_id", lesson_id).execute()

    transcription = None
    video_title = None

    if transcription_resp.data:
        transcription = transcription_resp.data[0]["transcription"]
        video_title = transcription_resp.data[0]["lesson_videos"]["title"]

    return {
        "course_id": lesson["modules"]["course_id"],
        "lesson_id": lesson_id,
        "module_name": lesson["modules"]["name"],
        "lesson_name": lesson["name"],
        "lesson_content": lesson["lesson_content"],
        "video_title": video_title,
        "video_transcription": transcription
    }

@router.get('/non_id/get_similar_lesson_chunks',
           description="Get similar lesson chunks")
async def get_similar_lesson_chunks(query: str,db: Client = Depends(get_supabase_client)):
    return similarity_check.get_similar_lesson_chunks(query, db)