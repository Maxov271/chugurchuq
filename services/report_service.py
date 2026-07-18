"""
services/report_service.py
-----------------------------
Foydalanuvchi yuborgan hisobotlarni qabul qilish, ma'lumotlar bazasiga
saqlash, administratorga yuborish va "XABARLARNI BOSHQARISH" talabiga
ko'ra foydalanuvchi chatidan eslatma/hisobot/tugmalarni avtomatik
o'chirish bilan shug'ullanadi.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from telebot.async_telebot import AsyncTeleBot
from telebot.apihelper import ApiTelegramException

from config import settings
from database.queries import activity_repo, message_repo, reminder_repo, statistics_repo
from keyboards.admin_keyboards import report_item_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)

# message.content_type -> ichki media_type nomi
MEDIA_TYPE_MAP = {
    "text": "text",
    "photo": "photo",
    "video": "video",
    "audio": "audio",
    "voice": "voice",
    "document": "document",
    "location": "location",
    "contact": "contact",
}


class ReportService:
    async def _safe_delete(self, bot: AsyncTeleBot, chat_id: int, message_id: int | None) -> None:
        if not message_id:
            return
        try:
            await bot.delete_message(chat_id, message_id)
        except ApiTelegramException as exc:
            # Xabar allaqachon o'chirilgan yoki 48 soatdan eski bo'lishi mumkin —
            # Telegram API cheklovi, xato jiddiy emas.
            logger.debug("Xabarni o'chirib bo'lmadi (chat=%s, msg=%s): %s", chat_id, message_id, exc)

    def _extract_content(self, message) -> tuple[str, str | None, str | None]:
        """Kelgan xabar turidan (media_type, file_id, matn/izoh) ni ajratadi."""
        content_type = message.content_type
        media_type = MEDIA_TYPE_MAP.get(content_type, content_type)

        file_id: str | None = None
        text: str | None = None

        if content_type == "text":
            text = message.text
        elif content_type == "photo":
            file_id = message.photo[-1].file_id
            text = message.caption
        elif content_type == "video":
            file_id = message.video.file_id
            text = message.caption
        elif content_type == "audio":
            file_id = message.audio.file_id
            text = message.caption
        elif content_type == "voice":
            file_id = message.voice.file_id
        elif content_type == "document":
            file_id = message.document.file_id
            text = message.caption
        elif content_type == "location":
            loc = message.location
            text = f"{loc.latitude},{loc.longitude}"
        elif content_type == "contact":
            c = message.contact
            text = f"{c.first_name} {c.phone_number}"

        return media_type, file_id, text

    async def handle_incoming_report(
        self, bot: AsyncTeleBot, message, user_row: sqlite3.Row, last_reminder_msg_id: int | None
    ) -> None:
        media_type, file_id, text = self._extract_content(message)

        message_id = await message_repo.create(
            user_id=user_row["id"],
            telegram_id=user_row["telegram_id"],
            internal_id=user_row["internal_id"],
            media_type=media_type,
            file_id=file_id,
            content=text,
            user_msg_id=message.message_id,
        )

        await reminder_repo.mark_responded(user_row["id"])
        await activity_repo.add(user_row["id"], "report_sent", f"type={media_type}")

        from datetime import date
        today = date.today()
        await statistics_repo.upsert_increment(
            user_row["id"], "daily", today.isoformat(), reports_delta=1
        )
        await statistics_repo.upsert_increment(
            user_row["id"], "weekly", f"{today.isocalendar().year}-W{today.isocalendar().week:02d}",
            reports_delta=1,
        )
        await statistics_repo.upsert_increment(
            user_row["id"], "monthly", today.strftime("%Y-%m"), reports_delta=1
        )

        await self._forward_to_admins(bot, message, user_row, message_id, media_type, text)

        # Foydalanuvchi chatini tozalash: eslatma + hisobot + tugmalar
        await self._safe_delete(bot, user_row["telegram_id"], last_reminder_msg_id)
        await self._safe_delete(bot, user_row["telegram_id"], message.message_id)

        logger.info("Yangi hisobot saqlandi: %s (%s)", user_row["internal_id"], media_type)

    async def _forward_to_admins(
        self, bot: AsyncTeleBot, message, user_row: sqlite3.Row, message_id: int, media_type: str, text: str | None
    ) -> None:
        header = (
            f"🆕 <b>Yangi hisobot</b>\n"
            f"👤 ID: <code>{user_row['internal_id']}</code>\n"
            f"📎 Turi: {media_type}\n"
        )
        kb = report_item_keyboard(message_id)

        for admin_id in settings.admin_ids:
            try:
                if media_type == "text":
                    sent = await bot.send_message(
                        admin_id, header + f"\n💬 {text or ''}", reply_markup=kb, parse_mode="HTML"
                    )
                else:
                    sent = await bot.copy_message(
                        admin_id, message.chat.id, message.message_id, reply_markup=kb
                    )
                    await bot.send_message(admin_id, header, parse_mode="HTML")
                if admin_id == settings.admin_ids[0]:
                    await message_repo.set_admin_msg_id(message_id, sent.message_id)
            except ApiTelegramException as exc:
                logger.error("Adminga xabar yuborilmadi (%s): %s", admin_id, exc)


report_service = ReportService()
