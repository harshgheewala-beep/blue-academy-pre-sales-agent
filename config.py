import os
import logging
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_CHAT_HISTORY_DB = os.path.join(BASE_DIR, 'agents_history.db')
SAVED_FILES = os.path.join(BASE_DIR, 'saved_files')
CHAT_WIDGET_EMBEDDING_DIR = Path(BASE_DIR, 'frontend-embedding')


MODEL={
    "fast-cheap":"gpt-4o-mini",
    "Complex-Cheap":"gpt-4.1-mini"
}

MODEL_CONFIG = {...}