import os
import logging
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_CHAT_HISTORY_DB = os.path.join(BASE_DIR, 'agents_history.db')
SAVED_FILES = os.path.join(BASE_DIR, 'saved_files')
CHAT_WIDGET_EMBEDDING_DIR = Path(BASE_DIR, 'frontend-embedding')


AVAILABLE_TABLES = [
    "courses",
    "course_chunks"
]
# print(BASE_DIR, AGENT_CHAT_HISTORY_DB, SAVED_FILES)
#
# LOGGING_CONFIG = {
#     "version": 1,
#     "disable_existing_loggers": False,
#
#     "formatters": {
#         "default": {
#             "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
#         }
#     },
#
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#             "formatter": "default",
#         }
#     },
#
#     "root": {
#         "level": "INFO",
#         "handlers": ["console"],
#     },
# }


MODEL={
    "fast-cheap":"gpt-4o-mini",
    "Complex-Cheap":"gpt-4.1-mini"
}

MODEL_CONFIG = {...}