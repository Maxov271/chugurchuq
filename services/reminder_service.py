"""
services/reminder_service.py
-------------------------------
Har bir foydalanuvchi uchun individual jadval (hafta kuni + vaqt)
asosida eslatma yuborish mantig'i. APScheduler tomonidan har daqiqada
chaqiriladigan tekshiruv shu yerda amalga oshiriladi.
"""

from __future__ import annotations

from datetime import datetime

from telebot.async_telebot import AsyncTeleBot
from telebot.apihelper import ApiTelegramException

from database.queries import reminder_repo, schedule_repo, statistics_repo, user_repo
from keyboards.user_keyboards import reminder_ack_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)

# Har bir foydalanuvchining oxirgi eslatma xabar id'sini xotirada saqlaymiz —
# hisobot kelganda shu xabarni foydalanuvchi chatidan o'chirish uchun kerak.
last_reminder_message: dict[int, int] = {}


class ReminderService:
    async def check_and_send_due_reminders(self, bot: AsyncTeleBot) -> None:
        """Joriy daqiqaga to'g'ri keladigan barcha jadvallarni tekshiradi
        va tegishli foydalanuvchilarga eslatma yuboradi."""
        now = datetime.now()
        current_weekday = now.weekday()  # 0=Dushanba
        current_time = now.strftime("%H:%M")

        schedules = await schedule_repo.get_all_active()
        due = [s for s in schedules if s["weekday"] == current_weekday and s["time"] == current_time]

        for schedule in due:
            user = await user_repo.get_by_id(schedule["user_id"])
            if not user or user["is_deleted"]:
                continue
            await self._send_reminder(bot, user, schedule)

    async def _send_reminder(self, bot: AsyncTeleBot, user, schedule) -> None:
        try:
            sent = await bot.send_message(
                user["telegram_id"],
                f"⏰ <b>Eslatma</b>\n\n{schedule['reminder_text']}",
                reply_markup=reminder_ack_keyboard(),
                parse_mode="HTML",
            )
            last_reminder_message[user["telegram_id"]] = sent.message_id
            await reminder_repo.log_sent(user["id"], schedule["id"], sent.message_id)

            from datetime import date
            today = date.today()
            await statistics_repo.upsert_increment(
                user["id"], "daily", today.isoformat(), reminders_delta=1
            )
            logger.info("Eslatma yuborildi: %s", user["internal_id"])
        except ApiTelegramException as exc:
            logger.error("Eslatma yuborilmadi (%s): %s", user["internal_id"], exc)


reminder_service = ReminderService()
