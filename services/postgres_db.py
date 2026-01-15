from __future__ import annotations
import json
import logging

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    delete,
    insert,
    select,
    text as sql_text,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from agents.items import TResponseInputItem
from agents.memory.session import SessionABC
import os
from dotenv import load_dotenv

logger = logging.getLogger("SQLAlchemy")
load_dotenv()


POSTGRES_URL = os.getenv("SQLALCHEMY_URL")
_engine: AsyncEngine | None = None


def init_async_engine(
    url: str = POSTGRES_URL,
    *,
    pool_size: int = 10,
    max_overflow: int = 20,
    echo: bool = False,
) -> AsyncEngine:
    global _engine
    if _engine is None:
        logger.info("Creating Async Engine...")
        _engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            echo=echo,
        )

    logger.info("Created Async Engine.")
    return _engine

def get_async_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("AsyncEngine not initialized")
    return _engine


async def dispose_async_engine() -> None:
    global _engine
    if _engine is not None:
        logger.info("Disposing Async Engine...")
        await _engine.dispose()
        _engine = None
        logger.info("Disposed Async Engine.")



class SQLAlchemySession(SessionABC):
    def __init__(
        self,
        session_id: str,
        *,
        create_tables: bool = False,
        sessions_table: str = "agent_sessions",
        messages_table: str = "agent_messages",
    ):
        self.session_id = session_id
        self._engine: AsyncEngine = get_async_engine()
        self._create_tables = create_tables

        self._metadata = MetaData()

        self._sessions = Table(
            sessions_table,
            self._metadata,
            Column("session_id", String, primary_key=True),
            Column(
                "created_at",
                TIMESTAMP,
                server_default=sql_text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            Column(
                "updated_at",
                TIMESTAMP,
                server_default=sql_text("CURRENT_TIMESTAMP"),
                onupdate=sql_text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

        self._messages = Table(
            messages_table,
            self._metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column(
                "session_id",
                String,
                ForeignKey(f"{sessions_table}.session_id", ondelete="CASCADE"),
                nullable=False,
            ),
            Column("message_data", Text, nullable=False),
            Column(
                "created_at",
                TIMESTAMP,
                server_default=sql_text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            Index(
                f"idx_{messages_table}_session_time",
                "session_id",
                "created_at",
            ),
        )

        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    async def _ensure_tables(self) -> None:
        if self._create_tables:
            async with self._engine.begin() as conn:
                await conn.run_sync(self._metadata.create_all)
            self._create_tables = False

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        await self._ensure_tables()

        async with self._session_factory() as sess:
            if limit is None:
                stmt = (
                    select(self._messages.c.message_data)
                    .where(self._messages.c.session_id == self.session_id)
                    .order_by(
                        self._messages.c.created_at.asc(),
                        self._messages.c.id.asc(),
                    )
                )
            else:
                stmt = (
                    select(self._messages.c.message_data)
                    .where(self._messages.c.session_id == self.session_id)
                    .order_by(
                        self._messages.c.created_at.desc(),
                        self._messages.c.id.desc(),
                    )
                    .limit(limit)
                )

            result = await sess.execute(stmt)
            rows = [r[0] for r in result.all()]
            if limit is not None:
                rows.reverse()

            return [json.loads(r) for r in rows]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        if not items:
            return

        await self._ensure_tables()


        payload = [
                {"session_id": self.session_id, "message_data": json.dumps(i)}
                for i in items if not isinstance(items, dict)
            ]


        async with self._session_factory() as sess:
            async with sess.begin():
                # await sess.execute(
                #     insert(self._sessions)
                #     .values(session_id=self.session_id)
                #     .prefix_with("OR IGNORE")
                # )
                await sess.execute(
                    pg_insert(self._sessions)
                    .values(session_id=self.session_id)
                    .on_conflict_do_nothing(index_elements=["session_id"])
                )

                await sess.execute(insert(self._messages), payload)
                await sess.execute(
                    update(self._sessions)
                    .where(self._sessions.c.session_id == self.session_id)
                    .values(updated_at=sql_text("CURRENT_TIMESTAMP"))
                )

    async def pop_item(self) -> TResponseInputItem | None:
        await self._ensure_tables()

        async with self._session_factory() as sess:
            async with sess.begin():
                stmt = (
                    delete(self._messages)
                    .where(
                        self._messages.c.id
                        == select(self._messages.c.id)
                        .where(self._messages.c.session_id == self.session_id)
                        .order_by(
                            self._messages.c.created_at.desc(),
                            self._messages.c.id.desc(),
                        )
                        .limit(1)
                        .scalar_subquery()
                    )
                    .returning(self._messages.c.message_data)
                )

                res = await sess.execute(stmt)
                row = res.scalar_one_or_none()
                return json.loads(row) if row else None

    async def clear_session(self) -> None:
        await self._ensure_tables()

        async with self._session_factory() as sess:
            async with sess.begin():
                await sess.execute(
                    delete(self._messages).where(
                        self._messages.c.session_id == self.session_id
                    )
                )
                await sess.execute(
                    delete(self._sessions).where(
                        self._sessions.c.session_id == self.session_id
                    )
                )

    def close(self) -> None:
        # Logical close only
        pass

