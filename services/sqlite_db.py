import asyncio
import json
import sqlite3
from pathlib import Path
from threading import Lock
import logging

from agents import SessionABC, TResponseInputItem

_conn: sqlite3.Connection | None = None
_db_lock = Lock()
SQLITE_SESSION_TABLE: str = "agent_sessions"
SQLITE_MESSAGE_TABLE: str = "agent_messages"

logger = logging.getLogger("SQLite DB Handler")


def init_sqlite(db_path: str | Path):
    global _conn
    logger.info("Initializing SQLite database...")
    if _conn is None:
        _conn = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
    logger.info(f"SQlite Database Connected.")
    return _conn


def get_conn() -> sqlite3.Connection:
    assert _conn is not None, "SQLite not initialized"
    return _conn


def get_lock() -> Lock:
    return _db_lock


def close_sqlite():
    logger.info("Closing SQLite database...")
    global _conn
    if _conn:
        _conn.close()
        _conn = None
    logger.info("SQLite database closed.")


def init_sqlite_db():
    """
    Initializing SQLite Database with Pre-Loaded Tables

    :return:
    """

    logger.info("Initializing SQLite database tables...")
    _conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {SQLITE_SESSION_TABLE} (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    _conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SQLITE_MESSAGE_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES {SQLITE_SESSION_TABLE} (session_id)
                ON DELETE CASCADE
        )
    """
    )

    _conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{SQLITE_MESSAGE_TABLE}_session_id
        ON {SQLITE_MESSAGE_TABLE} (session_id, created_at)
    """
    )

    _conn.commit()

    logger.info("SQLite database tables initialized.")


class CustomSQLiteSession(SessionABC):
    """
    Custom SQLite Session for Agent Memory Management
    """

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_items(self, limit: int = None):
        """Retrieve the conversation history for this session.

           Args:
               limit: Maximum number of items to retrieve. If None, retrieves all items.
                      When specified, returns the latest N items in chronological order.

           Returns:
               List of input items representing the conversation history
           """

        def _get_items_sync():
            with get_lock():
                if limit is None:
                    cur = get_conn().execute(
                        f"""
                           SELECT message_data
                           FROM {SQLITE_MESSAGE_TABLE}
                           WHERE session_id = ?
                           ORDER BY created_at ASC
                           """,
                        (self.session_id,),
                    )
                    rows = cur.fetchall()
                else:
                    cur = get_conn().execute(
                        f"""
                           SELECT message_data
                           FROM {SQLITE_MESSAGE_TABLE}
                           WHERE session_id = ?
                           ORDER BY created_at DESC
                           LIMIT ?
                           """,
                        (self.session_id, limit),
                    )
                    rows = list(reversed(cur.fetchall()))

                return [json.loads(r[0]) for r in rows]

        return await asyncio.to_thread(_get_items_sync)

    async def add_items(self, items):
        """Add new items to the conversation history.

        Args:
            items: List of input items to add to the history
        """

        if not items:
            return

        def _add_items_sync():
            with get_lock():
                conn = get_conn()
                with conn:
                    conn.execute(
                        f"INSERT OR IGNORE INTO {SQLITE_SESSION_TABLE} (session_id) VALUES (?)",
                        (self.session_id,),
                    )
                    conn.executemany(
                        f"""
                           INSERT INTO {SQLITE_MESSAGE_TABLE}
                           (session_id, message_data)
                           VALUES (?, ?)
                           """,
                        [(self.session_id, json.dumps(i)) for i in items],
                    )

        await asyncio.to_thread(_add_items_sync)

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item from the session.

        Returns:
            The most recent item if it exists, None if the session is empty
        """

        def _pop_item_sync():
            with get_lock():
                conn = get_conn()
                # Use DELETE with RETURNING to atomically delete and return the most recent item
                with conn:
                    cursor = conn.execute(
                        f"""
                           DELETE FROM {SQLITE_MESSAGE_TABLE}
                           WHERE id = (
                               SELECT id FROM {SQLITE_MESSAGE_TABLE}
                               WHERE session_id = ?
                               ORDER BY created_at DESC
                               LIMIT 1
                           )
                           RETURNING message_data
                           """,
                        (self.session_id,),
                    )

                    result = cursor.fetchone()

                if result:
                    message_data = result[0]
                    try:
                        item = json.loads(message_data)
                        return item
                    except json.JSONDecodeError:
                        return None

                return None

        return await asyncio.to_thread(_pop_item_sync)

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        ...

    def close(self):
        # NO-OP: logical close only
        pass
