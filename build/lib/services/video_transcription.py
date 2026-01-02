import os
import tempfile
import subprocess
from faster_whisper import WhisperModel
from logging import Logger
import time
from datetime import datetime


model = WhisperModel("medium",device="cuda")


async def extract_audio_from_video(video_bytes: bytes, suffix: str) -> bytes:
    logger = Logger(name="Video Audio Extraction Logs")
    start_time = time.time()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_video:
        tmp_video.write(video_bytes)
        video_path = tmp_video.name

    audio_path = video_path.replace(suffix, ".wav")

    # Extract audio using ffmpeg
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",           # no video
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]


    logger.info(f"Extracting audio... {datetime.now()}")
    print(f"Extracting audio... {datetime.now()}")
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info(f"Audio Extracted {datetime.now()}")
    print(f"Audio Extracted {datetime.now()}")
    end_time = time.time()

    logger.info(f"Audio Extraction time :{end_time - start_time}")
    print(f"Audio Extraction time :{end_time - start_time}")
    # Read audio bytes
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()



    # cleanup
    os.remove(video_path)
    os.remove(audio_path)

    return audio_bytes


async def transcribe_audio(audio_bytes: bytes)->str:
    logger = Logger(name="Audio Transcription Logs")
    start_time = time.time()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
        temp.write(audio_bytes)
        temp_path = temp.name

    logger.info(f"Transcribing audio... {datetime.now()}")
    print(f"Transcribing audio... {datetime.now()}")
    segments, info = model.transcribe(temp_path)
    logger.info(f"Audio Transcribed {datetime.now()}")
    print(f"Audio Transcribed {datetime.now()}")
    end_time = time.time()
    logger.info(f"Audio Transcription time :{end_time - start_time}")
    print(f"Audio Transcription time :{end_time - start_time}")


    segments_text = [segment.text.strip() for segment in segments]

    start_time = time.time()

    full_text = " ".join(segments_text).strip()
    end_time = time.time()
    print(f"Joined Audio Text segments in {end_time - start_time}")

    return full_text



async def video_transcription_pipeline(video_bytes: bytes, suffix: str)->str:
    audio_bytes = await extract_audio_from_video(video_bytes, suffix)
    transcript = await transcribe_audio(audio_bytes)

    return transcript
