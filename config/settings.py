"""
config/settings.py
-------------------
Loyihaning markaziy sozlamalari. Barcha maxfiy ma'lumotlar (BOT_TOKEN,
ADMIN_ID) faqat .env fayldan o'qiladi va hech qachon kod ichiga yozilmaydi.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Loyiha ildiz papkasi
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# .env faylini yuklash
load_dotenv(BASE_DIR / ".env")


def _parse_admin_ids(raw: str | None, fallback: str | None) -> list[int]:
    """ADMIN_IDS yoki ADMIN_ID qiymatlaridan int ro'yxat hosil qiladi."""
    source = raw or fallback or ""
    ids: list[int] = []
    for part in source.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


@dataclass(frozen=True, slots=True)
class Settings:
    """Bot uchun barcha global sozlamalarni saqlovchi immutable dataclass."""

    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admin_ids: list[int] = field(
        default_factory=lambda: _parse_admin_ids(
            os.getenv("ADMIN_IDS"), os.getenv("ADMIN_ID")
        )
    )

    # Papkalar
    base_dir: Path = BASE_DIR
    db_path: Path = BASE_DIR / os.getenv("DB_PATH", "database/bot.db")
    media_dir: Path = BASE_DIR / "media"
    logs_dir: Path = BASE_DIR / "logs"
    exports_dir: Path = BASE_DIR / "exports"
    backups_dir: Path = BASE_DIR / "backups"
    templates_dir: Path = BASE_DIR / "templates"

    # Backup vaqti (har kuni)
    backup_hour: int = field(default_factory=lambda: int(os.getenv("BACKUP_HOUR", "3")))
    backup_minute: int = field(default_factory=lambda: int(os.getenv("BACKUP_MINUTE", "0")))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: Path = BASE_DIR / os.getenv("LOG_FILE", "logs/bot.log")

    # Ichki identifikator prefiksi (CH-001, CH-002, ...)
    id_prefix: str = "CH"
    id_padding: int = 3

    def validate(self) -> None:
        """Majburiy sozlamalar mavjudligini tekshiradi."""
        if not self.bot_token:
            raise RuntimeError(
                "BOT_TOKEN topilmadi. .env faylida BOT_TOKEN=... ko'rsating."
            )
        if not self.admin_ids:
            raise RuntimeError(
                "ADMIN_ID/ADMIN_IDS topilmadi. .env faylida kamida bitta admin ID ko'rsating."
            )

    def ensure_dirs(self) -> None:
        """Kerakli papkalarni yaratadi (agar mavjud bo'lmasa)."""
        for path in (
            self.media_dir,
            self.logs_dir,
            self.exports_dir,
            self.backups_dir,
            self.db_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
