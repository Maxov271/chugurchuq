"""
services/user_service.py
--------------------------
Foydalanuvchilarni ro'yxatga olish, statuslarni yangilash va
"e'tibor talab qiluvchi foydalanuvchilar" ro'yxatini shakllantirish
bilan bog'liq biznes-mantiq.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from config import settings
from database.queries import (
    activity_repo,
    message_repo,
    reminder_repo,
    user_repo,
)
from utils.logger import get_logger

logger = get_logger(__name__)

STATUS_FAOL = "Faol"
STATUS_MONITORING = "Monitoring holatida"
STATUS_LOW_ACTIVITY = "Faolligi past"
STATUS_TEMP_INACTIVE = "Vaqtincha faol emas"
STATUS_DELETED = "O'chirilgan"


@dataclass(slots=True)
class AttentionEntry:
    internal_id: str
    full_name: str | None
    reason: str
    reminders_sent: int
    last_activity: str | None
    total_replies: int


class UserService:
    async def register_user(self, telegram_id: int, full_name: str, username: str | None) -> sqlite3.Row:
        existing = await user_repo.get_by_telegram_id(telegram_id)
        if existing:
            return existing

        internal_id = await user_repo.next_internal_id(settings.id_prefix, settings.id_padding)
        await user_repo.create(telegram_id, internal_id, full_name, username)
        await activity_repo.add(
            (await user_repo.get_by_telegram_id(telegram_id))["id"],
            "registered",
            f"internal_id={internal_id}",
        )
        logger.info("Yangi foydalanuvchi ro'yxatdan o'tkazildi: %s (%s)", internal_id, telegram_id)
        return await user_repo.get_by_telegram_id(telegram_id)

    async def touch_activity(self, user_row: sqlite3.Row) -> None:
        await user_repo.update_last_activity(user_row["id"])
        if user_row["status"] in (STATUS_LOW_ACTIVITY, STATUS_TEMP_INACTIVE, STATUS_MONITORING):
            await user_repo.update_status(user_row["id"], STATUS_FAOL)

    async def recompute_status(self, user_row: sqlite3.Row) -> str:
        """Foydalanuvchi faolligiga qarab statusni qayta hisoblaydi."""
        user_id = user_row["id"]
        unanswered = await reminder_repo.count_consecutive_unanswered(user_id)

        if user_row["last_activity"] is None:
            new_status = STATUS_MONITORING
        elif unanswered >= 3:
            new_status = STATUS_TEMP_INACTIVE
        else:
            row = await user_repo.inactive_since(30)
            is_low = any(u["id"] == user_id for u in row)
            new_status = STATUS_LOW_ACTIVITY if is_low else STATUS_FAOL

        if new_status != user_row["status"]:
            await user_repo.update_status(user_id, new_status)
        return new_status

    async def build_attention_list(self) -> list[AttentionEntry]:
        """3 marta ketma-ket javob bermagan yoki uzoq faolligi bo'lmagan
        foydalanuvchilar ro'yxatini shakllantiradi."""
        entries: list[AttentionEntry] = []
        users = await user_repo.get_all()

        for user in users:
            unanswered = await reminder_repo.count_consecutive_unanswered(user["id"])
            total_reminders = await reminder_repo.count_for_user(user["id"])
            total_reports = await message_repo.count_by_user(user["id"])

            reasons = []
            if unanswered >= 3:
                reasons.append(f"ketma-ket {unanswered} ta eslatmaga javob bermagan")

            inactive_30 = await user_repo.inactive_since(30)
            if any(u["id"] == user["id"] for u in inactive_30):
                reasons.append("30 kundan beri faollik ko'rsatmagan")

            if reasons:
                entries.append(
                    AttentionEntry(
                        internal_id=user["internal_id"],
                        full_name=user["full_name"],
                        reason="; ".join(reasons),
                        reminders_sent=total_reminders,
                        last_activity=user["last_activity"],
                        total_replies=total_reports,
                    )
                )
        return entries


user_service = UserService()
