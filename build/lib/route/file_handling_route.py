import ffmpeg.video
from fastapi import APIRouter, UploadFile, File
from fastapi import Response
import subprocess

from starlette.responses import FileResponse

from config import SAVED_FILES
from services.video_transcription import video_transcription_pipeline

router = APIRouter(
    prefix="/file_handling",
    tags=["File Handling Route"],
)


@router.post("/file_check")
async def file_check(file: UploadFile = File(...)):
    return {
        "File Name": file.filename,
        "Content-Type": file.content_type
    }


@router.post("/get_video_transcription")
async def get_video_transcription(video: UploadFile = File(...)):
    video_bytes = await video.read()
    suffix = "."+video.filename.split(".")[-1]
    transcript = await video_transcription_pipeline(video_bytes,suffix=suffix)
    return {
        "transcript": transcript
    }