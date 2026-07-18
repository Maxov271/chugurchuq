"""
database/connection.py
-----------------------
SQLite3 (standart kutubxona) ustidan asinxron wrapper. sqlite3 modulining
o'zi sinxron bo'lgani uchun barcha so'rovlar asyncio.to_thread orqali
alohida threadda bajariladi va event loop bloklanmaydi. Yagona connection
va asyncio.Lock orqali thread-xavfsizlik ta'minlanadi (WAL rejimi yordamida
o'qish/yozish parallelligi oshiriladi).
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from config import settings
from database.models import SCHEMA_STATEMENTS
from utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite3 ustida yagona, thread-xavfsiz asinxron interfeys."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or settings.db_path
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    # Ulanish
    # ------------------------------------------------------------------ #
    def _connect_sync(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA synchronous = NORMAL;")

    async def connect(self) -> None:
        if self._conn is None:
            await asyncio.to_thread(self._connect_sync)
            logger.info("SQLite ulanishi ochildi: %s", self._db_path)

    async def close(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
            logger.info("SQLite ulanishi yopildi.")

    # ------------------------------------------------------------------ #
    # Sxema
    # ------------------------------------------------------------------ #
    async def init_schema(self) -> None:
        """Barcha jadvallarni (agar mavjud bo'lmasa) yaratadi."""
        await self.connect()
        for statement in SCHEMA_STATEMENTS:
            await self.execute(statement)
        logger.info("Ma'lumotlar bazasi sxemasi tayyor (%d jadval).", len(SCHEMA_STATEMENTS))

    # ------------------------------------------------------------------ #
    # So'rovlar
    # ------------------------------------------------------------------ #
    def _execute_sync(self, query: str, params: Iterable[Any]) -> sqlite3.Cursor:
        assert self._conn is not None
        cur = self._conn.execute(query, tuple(params))
        self._conn.commit()
        return cur

    def _executemany_sync(self, query: str, seq_of_params: Iterable[Iterable[Any]]) -> None:
        assert self._conn is not None
        self._conn.executemany(query, [tuple(p) for p in seq_of_params])
        self._conn.commit()

    async def execute(self, query: str, params: Iterable[Any] = ()) -> int:
        """INSERT/UPDATE/DELETE bajaradi, lastrowid qaytaradi."""
        async with self._lock:
            cur = await asyncio.to_thread(self._execute_sync, query, params)
            return cur.lastrowid

    async def executemany(self, query: str, seq_of_params: Iterable[Iterable[Any]]) -> None:
        async with self._lock:
            await asyncio.to_thread(self._executemany_sync, query, seq_of_params)

    async def fetch_one(self, query: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        async with self._lock:
            cur = await asyncio.to_thread(self._execute_sync, query, params)
            return cur.fetchone()

    async def fetch_all(self, query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        async with self._lock:
            cur = await asyncio.to_thread(self._execute_sync, query, params)
            return cur.fetchall()


# Butun loyiha bo'ylab ishlatiladigan yagona (singleton) instance
db = Database()
