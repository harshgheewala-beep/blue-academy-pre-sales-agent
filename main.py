import os
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
from agents import set_trace_processors
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langsmith.integrations.openai_agents_sdk import OpenAIAgentsTracingProcessor
from config import CHAT_WIDGET_EMBEDDING_DIR
from logging_config import setup_logging
from route import agent_route, internal_route
from services.auth_middleware import AuthMiddleware
from fastapi.staticfiles import StaticFiles

from services.redis_service import disconnect_redis
from services.weaviate import init_weaviate, close_weaviate

BASE_DIR = Path(__file__).resolve().parent
CHAT_EMBEDDING_DIR = BASE_DIR / "frontend-embedding"
FRONTEND_DIR = BASE_DIR / "frontend"



setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_trace_processors(
        processors=[OpenAIAgentsTracingProcessor(
            name="Sales Agent",
            project_name="Blue Academy",
            tags=["v2", "low_latency test"]
        )]
    )

    await init_weaviate()
    yield
    await disconnect_redis()
    await close_weaviate()


app = FastAPI(
    title="Blue Academy",
    description="This is just an example app",
    version="1.0",
    lifespan=lifespan
)


app.include_router(internal_route.router)
app.include_router(agent_route.router)
# app.include_router(course_route.router)
# app.include_router(module_route.router)
# app.include_router(lesson_route.router)
# app.include_router(file_handling_route.router)
# app.include_router(users_route.router)
# app.include_router(role_permission_route.router)
# app.include_router(auth_route.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)


app.add_middleware(AuthMiddleware)

app.mount(
    "/chat-widget",
    StaticFiles(directory=CHAT_WIDGET_EMBEDDING_DIR, html=True),
    name="embedding"
)

# app.mount("/app",
#           StaticFiles(directory=FRONTEND_DIR, html=True),
#           name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST"), port=5000)
