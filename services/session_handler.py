import asyncio
import os
import json
import threading
from agents.memory.sqlite_session import SQLiteSession
# from agents.extensions.memory import SQLAlchemySession
from dotenv import load_dotenv
import logging
from services.sqlite_db import CustomSQLiteSession
from services.postgres_db import SQLAlchemySession

load_dotenv()

logger = logging.getLogger("Session Manager")
DEV_MODE = (os.getenv("DEV_MODE",'False') == 'True')



async def get_custom_session(session_id: str)-> SQLAlchemySession | CustomSQLiteSession:
    if DEV_MODE:
        return CustomSQLiteSession(session_id)

    return SQLAlchemySession(session_id=session_id,
                             create_tables=True)



async def close_session(session) -> None:
    if session is None:
        return
    if hasattr(session, "close"):
        session.close()


class SessionManager:
    """Manages session lifecycle with guaranteed cleanup"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session = None


    async def __aenter__(self):
        """Create and return session"""
        self.session = await get_custom_session(self.session_id)
        return self.session


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session"""
        await close_session(self.session)
        return None
