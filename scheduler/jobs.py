"""
scheduler/jobs.py
------------------
APScheduler yordamida barcha vaqtli vazifalarni ro'yxatga oladi:
  * har daqiqada — foydalanuvchilar jadvaliga mos eslatmalarni yuborish;
  * har kuni belgilangan vaqtda — to'liq backup (database + media + logs).
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.async_telebot import AsyncTeleBot

from config import settings
from services.backup_service import backup_service
from services.reminder_service import reminder_service
from utils.logger import get_logger

logger = get_logger(__name__)


def setup_scheduler(bot: AsyncTeleBot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    scheduler.add_job(
        reminder_service.check_and_send_due_reminders,
        trigger=CronTrigger(second=0),  # har daqiqaning 0-soniyasida
        args=[bot],
        id="reminder_check",
        max_instances=1,
        misfire_grace_time=30,
        replace_existing=True,
    )

    scheduler.add_job(
        backup_service.run_full_backup,
        trigger=CronTrigger(hour=settings.backup_hour, minute=settings.backup_minute),
        id="daily_backup",
        max_instances=1,
        misfire_grace_time=3600,
        replace_existing=True,
    )

    logger.info("Scheduler sozlandi: eslatmalar (har daqiqa), backup (%02d:%02d)",
                settings.backup_hour, settings.backup_minute)
    return scheduler
