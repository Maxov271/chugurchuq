"""
database/queries.py
--------------------
Har bir jadval uchun repository klasslari. Bu qatlam SQL so'rovlarini
yashiradi va yuqori darajadagi servislarga toza (clean) interfeys taqdim
etadi (Repository Pattern, Clean Architecture).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from database.connection import db


# ========================================================================
# USERS
# ========================================================================
class UserRepository:
    async def create(self, telegram_id: int, internal_id: str, full_name: str, username: str | None) -> int:
        return await db.execute(
            """INSERT INTO users (telegram_id, internal_id, full_name, username)
               VALUES (?, ?, ?, ?)""",
            (telegram_id, internal_id, full_name, username),
        )

    async def get_by_telegram_id(self, telegram_id: int) -> sqlite3.Row | None:
        return await db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ? AND is_deleted = 0", (telegram_id,)
        )

    async def get_by_internal_id(self, internal_id: str) -> sqlite3.Row | None:
        return await db.fetch_one("SELECT * FROM users WHERE internal_id = ?", (internal_id,))

    async def get_by_id(self, user_id: int) -> sqlite3.Row | None:
        return await db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))

    async def get_all(self, include_deleted: bool = False) -> list[sqlite3.Row]:
        if include_deleted:
            return await db.fetch_all("SELECT * FROM users ORDER BY id")
        return await db.fetch_all("SELECT * FROM users WHERE is_deleted = 0 ORDER BY id")

    async def count(self) -> int:
        row = await db.fetch_one("SELECT COUNT(*) AS c FROM users WHERE is_deleted = 0")
        return row["c"] if row else 0

    async def next_internal_id(self, prefix: str, padding: int) -> str:
        row = await db.fetch_one("SELECT COUNT(*) AS c FROM users")
        seq = (row["c"] if row else 0) + 1
        return f"{prefix}-{seq:0{padding}d}"

    async def update_status(self, user_id: int, status: str) -> None:
        await db.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))

    async def update_last_activity(self, user_id: int) -> None:
        await db.execute(
            "UPDATE users SET last_activity = datetime('now') WHERE id = ?", (user_id,)
        )

    async def soft_delete(self, user_id: int) -> None:
        await db.execute(
            "UPDATE users SET is_deleted = 1, status = 'ochirilgan' WHERE id = ?", (user_id,)
        )

    async def inactive_since(self, days: int) -> list[sqlite3.Row]:
        return await db.fetch_all(
            """SELECT * FROM users
               WHERE is_deleted = 0
                 AND (last_activity IS NULL OR last_activity <= datetime('now', ?))
               ORDER BY last_activity ASC""",
            (f"-{days} days",),
        )

    async def search(self, query: str) -> list[sqlite3.Row]:
        like = f"%{query}%"
        return await db.fetch_all(
            """SELECT * FROM users
               WHERE is_deleted = 0
                 AND (full_name LIKE ? OR username LIKE ? OR internal_id LIKE ? OR CAST(telegram_id AS TEXT) LIKE ?)
               ORDER BY id""",
            (like, like, like, like),
        )


# ========================================================================
# ADMINS
# ========================================================================
class AdminRepository:
    async def add(self, telegram_id: int, full_name: str | None = None) -> int:
        return await db.execute(
            "INSERT OR IGNORE INTO admins (telegram_id, full_name) VALUES (?, ?)",
            (telegram_id, full_name),
        )

    async def get_all(self) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM admins ORDER BY id")

    async def is_admin(self, telegram_id: int) -> bool:
        row = await db.fetch_one("SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,))
        return row is not None


# ========================================================================
# MESSAGES (hisobotlar)
# ========================================================================
class MessageRepository:
    async def create(
        self,
        user_id: int,
        telegram_id: int,
        internal_id: str,
        media_type: str,
        file_id: str | None,
        content: str | None,
        report_type: str = "kunlik",
        user_msg_id: int | None = None,
    ) -> int:
        return await db.execute(
            """INSERT INTO messages
               (user_id, telegram_id, internal_id, media_type, file_id, content, report_type, user_msg_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, telegram_id, internal_id, media_type, file_id, content, report_type, user_msg_id),
        )

    async def set_admin_msg_id(self, message_id: int, admin_msg_id: int) -> None:
        await db.execute(
            "UPDATE messages SET admin_msg_id = ? WHERE id = ?", (admin_msg_id, message_id)
        )

    async def mark_read(self, message_id: int) -> None:
        await db.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,))
        await db.execute(
            """INSERT INTO read_status (message_id, is_read, read_at)
               VALUES (?, 1, datetime('now'))""",
            (message_id,),
        )

    async def mark_replied(self, message_id: int) -> None:
        await db.execute("UPDATE messages SET is_replied = 1 WHERE id = ?", (message_id,))

    async def get_by_id(self, message_id: int) -> sqlite3.Row | None:
        return await db.fetch_one("SELECT * FROM messages WHERE id = ?", (message_id,))

    async def get_today(self) -> list[sqlite3.Row]:
        return await db.fetch_all(
            "SELECT * FROM messages WHERE report_date = date('now') ORDER BY id DESC"
        )

    async def get_weekly(self) -> list[sqlite3.Row]:
        return await db.fetch_all(
            "SELECT * FROM messages WHERE report_date >= date('now', '-7 days') ORDER BY id DESC"
        )

    async def get_monthly(self) -> list[sqlite3.Row]:
        return await db.fetch_all(
            "SELECT * FROM messages WHERE report_date >= date('now', '-30 days') ORDER BY id DESC"
        )

    async def get_all(self) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM messages ORDER BY id DESC")

    async def get_unread(self) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM messages WHERE is_read = 0 ORDER BY id DESC")

    async def get_by_user(self, user_id: int, limit: int = 50) -> list[sqlite3.Row]:
        return await db.fetch_all(
            "SELECT * FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )

    async def count_by_user(self, user_id: int) -> int:
        row = await db.fetch_one(
            "SELECT COUNT(*) AS c FROM messages WHERE user_id = ?", (user_id,)
        )
        return row["c"] if row else 0


# ========================================================================
# SCHEDULES (eslatma jadvali)
# ========================================================================
class ScheduleRepository:
    async def add(self, user_id: int, weekday: int, time_str: str, reminder_text: str) -> int:
        return await db.execute(
            """INSERT INTO schedules (user_id, weekday, time, reminder_text)
               VALUES (?, ?, ?, ?)""",
            (user_id, weekday, time_str, reminder_text),
        )

    async def get_by_user(self, user_id: int) -> list[sqlite3.Row]:
        return await db.fetch_all(
            "SELECT * FROM schedules WHERE user_id = ? AND is_active = 1 ORDER BY weekday, time",
            (user_id,),
        )

    async def get_all_active(self) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM schedules WHERE is_active = 1")

    async def deactivate(self, schedule_id: int) -> None:
        await db.execute("UPDATE schedules SET is_active = 0 WHERE id = ?", (schedule_id,))

    async def delete(self, schedule_id: int) -> None:
        await db.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))


# ========================================================================
# REMINDERS
# ========================================================================
class ReminderRepository:
    async def log_sent(self, user_id: int, schedule_id: int | None, chat_message_id: int | None) -> int:
        return await db.execute(
            """INSERT INTO reminders (user_id, schedule_id, chat_message_id)
               VALUES (?, ?, ?)""",
            (user_id, schedule_id, chat_message_id),
        )

    async def mark_responded(self, user_id: int) -> None:
        await db.execute(
            """UPDATE reminders SET responded = 1
               WHERE user_id = ? AND id = (
                   SELECT id FROM reminders WHERE user_id = ? ORDER BY id DESC LIMIT 1
               )""",
            (user_id, user_id),
        )

    async def count_consecutive_unanswered(self, user_id: int) -> int:
        rows = await db.fetch_all(
            "SELECT responded FROM reminders WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (user_id,),
        )
        count = 0
        for row in rows:
            if row["responded"] == 0:
                count += 1
            else:
                break
        return count

    async def count_for_user(self, user_id: int) -> int:
        row = await db.fetch_one(
            "SELECT COUNT(*) AS c FROM reminders WHERE user_id = ?", (user_id,)
        )
        return row["c"] if row else 0


# ========================================================================
# STATISTICS
# ========================================================================
class StatisticsRepository:
    async def upsert_increment(
        self, user_id: int, period_type: str, period_value: str, reports_delta: int = 0,
        reminders_delta: int = 0, no_response_delta: int = 0,
    ) -> None:
        await db.execute(
            """INSERT INTO statistics (user_id, period_type, period_value, reports_count, reminders_count, no_response_count)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, period_type, period_value) DO UPDATE SET
                 reports_count = reports_count + excluded.reports_count,
                 reminders_count = reminders_count + excluded.reminders_count,
                 no_response_count = no_response_count + excluded.no_response_count,
                 updated_at = datetime('now')""",
            (user_id, period_type, period_value, reports_delta, reminders_delta, no_response_delta),
        )

    async def top_active(self, limit: int = 10) -> list[sqlite3.Row]:
        return await db.fetch_all(
            """SELECT u.*, COUNT(m.id) AS total_reports
               FROM users u LEFT JOIN messages m ON m.user_id = u.id
               WHERE u.is_deleted = 0
               GROUP BY u.id ORDER BY total_reports DESC LIMIT ?""",
            (limit,),
        )

    async def top_inactive(self, limit: int = 10) -> list[sqlite3.Row]:
        return await db.fetch_all(
            """SELECT u.*, COUNT(m.id) AS total_reports
               FROM users u LEFT JOIN messages m ON m.user_id = u.id
               WHERE u.is_deleted = 0
               GROUP BY u.id ORDER BY total_reports ASC LIMIT ?""",
            (limit,),
        )


# ========================================================================
# SETTINGS
# ========================================================================
class SettingsRepository:
    async def get(self, key: str, default: str | None = None) -> str | None:
        row = await db.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default

    async def set(self, key: str, value: str) -> None:
        await db.execute(
            """INSERT INTO settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, value),
        )

    async def get_all(self) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM settings ORDER BY key")


# ========================================================================
# EXPORTS / BACKUPS / NOTIFICATIONS / LOGS / ACTIVITY
# ========================================================================
class ExportRepository:
    async def log(self, admin_id: int, export_type: str, filter_type: str, file_path: str) -> int:
        return await db.execute(
            """INSERT INTO exports (admin_id, export_type, filter_type, file_path)
               VALUES (?, ?, ?, ?)""",
            (admin_id, export_type, filter_type, file_path),
        )

    async def history(self, limit: int = 20) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM exports ORDER BY id DESC LIMIT ?", (limit,))


class BackupRepository:
    async def log(self, backup_type: str, file_path: str, status: str = "success") -> int:
        return await db.execute(
            "INSERT INTO backups (backup_type, file_path, status) VALUES (?, ?, ?)",
            (backup_type, file_path, status),
        )

    async def history(self, limit: int = 20) -> list[sqlite3.Row]:
        return await db.fetch_all("SELECT * FROM backups ORDER BY id DESC LIMIT ?", (limit,))


class NotificationRepository:
    async def create(self, notification_type: str, content: str, user_id: int | None = None, admin_id: int | None = None) -> int:
        return await db.execute(
            """INSERT INTO notifications (admin_id, user_id, notification_type, content)
               VALUES (?, ?, ?, ?)""",
            (admin_id, user_id, notification_type, content),
        )

    async def mark_sent(self, notification_id: int) -> None:
        await db.execute("UPDATE notifications SET is_sent = 1 WHERE id = ?", (notification_id,))


class LogRepository:
    async def add(self, level: str, module: str, message: str) -> None:
        await db.execute(
            "INSERT INTO logs (level, module, message) VALUES (?, ?, ?)",
            (level, module, message),
        )


class UserActivityRepository:
    async def add(self, user_id: int, action: str, details: str | None = None) -> None:
        await db.execute(
            "INSERT INTO user_activity (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details),
        )

    async def get_by_user(self, user_id: int, limit: int = 50) -> list[sqlite3.Row]:
        return await db.fetch_all(
            "SELECT * FROM user_activity WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )


class MediaRepository:
    async def add(self, message_id: int, file_id: str, media_type: str, local_path: str | None = None) -> int:
        return await db.execute(
            """INSERT INTO media_files (message_id, file_id, media_type, local_path)
               VALUES (?, ?, ?, ?)""",
            (message_id, file_id, media_type, local_path),
        )


# Repository instansiyalari (butun loyiha bo'ylab qayta ishlatiladi)
user_repo = UserRepository()
admin_repo = AdminRepository()
message_repo = MessageRepository()
schedule_repo = ScheduleRepository()
reminder_repo = ReminderRepository()
statistics_repo = StatisticsRepository()
settings_repo = SettingsRepository()
export_repo = ExportRepository()
backup_repo = BackupRepository()
notification_repo = NotificationRepository()
log_repo = LogRepository()
activity_repo = UserActivityRepository()
media_repo = MediaRepository()
