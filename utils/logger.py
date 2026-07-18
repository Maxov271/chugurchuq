"""
utils/logger.py
----------------
Butun loyiha uchun markazlashtirilgan logging konfiguratsiyasi.
Konsolga va faylga (rotatsiya bilan) yozadi.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FILE = Path(
    os.getenv("LOG_FILE", str(Path(__file__).resolve().parent.parent / "logs" / "bot.log"))
)
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_configured_loggers: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """Berilgan nom uchun konfiguratsiya qilingan logger qaytaradi."""
    logger = logging.getLogger(name)

    if name in _configured_loggers:
        return logger

    logger.setLevel(_LOG_LEVEL)
    logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(_FORMATTER)
    logger.addHandler(file_handler)

    _configured_loggers.add(name)
    return logger
