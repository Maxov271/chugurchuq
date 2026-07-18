"""
services/backup_service.py
-----------------------------
Har kuni (yoki admin so'rovi bo'yicha) database, media va logs
papkalarining zaxira nusxasini (backup) yaratadi.
"""

from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from config import settings
from database.queries import backup_repo
from utils.logger import get_logger

logger = get_logger(__name__)


class BackupService:
    def _stamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    async def backup_database(self) -> Path:
        stamp = self._stamp()
        dest = settings.backups_dir / f"db_backup_{stamp}.db"
        shutil.copy2(settings.db_path, dest)
        await backup_repo.log("database", str(dest))
        logger.info("Database backup yaratildi: %s", dest)
        return dest

    def _zip_dir(self, source_dir: Path, dest_zip: Path) -> None:
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(source_dir))

    async def backup_media(self) -> Path:
        stamp = self._stamp()
        dest = settings.backups_dir / f"media_backup_{stamp}.zip"
        has_files = settings.media_dir.exists() and any(settings.media_dir.iterdir())
        if has_files:
            self._zip_dir(settings.media_dir, dest)
        else:
            with zipfile.ZipFile(dest, "w"):
                pass
        await backup_repo.log("media", str(dest))
        logger.info("Media backup yaratildi: %s", dest)
        return dest

    async def backup_logs(self) -> Path:
        stamp = self._stamp()
        dest = settings.backups_dir / f"logs_backup_{stamp}.zip"
        if settings.logs_dir.exists() and any(settings.logs_dir.iterdir()):
            self._zip_dir(settings.logs_dir, dest)
        else:
            with zipfile.ZipFile(dest, "w"):
                pass
        await backup_repo.log("logs", str(dest))
        logger.info("Logs backup yaratildi: %s", dest)
        return dest

    async def run_full_backup(self) -> dict[str, Path]:
        return {
            "database": await self.backup_database(),
            "media": await self.backup_media(),
            "logs": await self.backup_logs(),
        }


backup_service = BackupService()
