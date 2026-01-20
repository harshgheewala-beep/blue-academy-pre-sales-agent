import os
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
from agents import set_trace_processors

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langsmith.integrations.openai_agents_sdk import OpenAIAgentsTracingProcessor
from starlette.responses import JSONResponse

from config import CHAT_WIDGET_EMBEDDING_DIR
from logging_config import setup_logging
from route import agent_route, internal_route
from services.auth_middleware import LogMiddleware
from fastapi.staticfiles import StaticFiles

from services.postgres_db import init_async_engine, dispose_async_engine
from services.redis_service import disconnect_redis
from services.sqlite_db import init_sqlite, init_sqlite_db, close_sqlite
from services.weaviate_service import init_weaviate, close_weaviate

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / 'agents_history.db'
CHAT_EMBEDDING_DIR = BASE_DIR / "frontend-embedding"
FRONTEND_DIR = BASE_DIR / "frontend"
POSTGRES_URI = os.getenv("SQLALCHEMY_URL")


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
    init_sqlite(SQLITE_DB_PATH)
    init_sqlite_db()
    init_async_engine(
        url=POSTGRES_URI,
        pool_size=10,
        max_overflow=20,
        echo=False
    )
    
    yield

    await disconnect_redis()
    await close_weaviate()
    close_sqlite()
    await dispose_async_engine()



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


app.add_middleware(LogMiddleware)

app.mount(
    "/chat-widget",
    StaticFiles(directory=CHAT_WIDGET_EMBEDDING_DIR, html=True),
    name="embedding"
)


@app.get('/health')
async def health():
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )


if __name__ == "__main__":
    uvicorn.run(app,host='0.0.0.0', port=5000)
