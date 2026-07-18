"""
main.py
--------
Botning kirish nuqtasi (entry point). Quyidagi tartibda ishga tushadi:
  1. Sozlamalarni tekshiradi va kerakli papkalarni yaratadi;
  2. Ma'lumotlar bazasi sxemasini tayyorlaydi;
  3. .env dagi adminlarni admins jadvaliga qo'shadi;
  4. AsyncTeleBot instansiyasini yaratadi va handlerlarni ro'yxatdan o'tkazadi;
  5. APScheduler'ni ishga tushiradi (eslatmalar + backup);
  6. Botni polling rejimida ishga tushiradi.
"""

from __future__ import annotations

import asyncio
import signal

from telebot.async_telebot import AsyncTeleBot

from config import settings
from database.connection import db
from database.queries import admin_repo
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers
from scheduler.jobs import setup_scheduler
from utils.logger import get_logger

logger = get_logger("main")


async def bootstrap() -> AsyncTeleBot:
    settings.validate()
    settings.ensure_dirs()

    await db.init_schema()

    for admin_id in settings.admin_ids:
        await admin_repo.add(admin_id)
    logger.info("Adminlar ro'yxati sinxronlashtirildi: %s", settings.admin_ids)

    bot = AsyncTeleBot(settings.bot_token, parse_mode="HTML")

    register_admin_handlers(bot)
    register_user_handlers(bot)

    return bot


async def main() -> None:
    bot = await bootstrap()
    scheduler = setup_scheduler(bot)
    scheduler.start()

    logger.info("Bot ishga tushdi (polling rejimi).")

    stop_event = asyncio.Event()

    def _handle_stop(*_args) -> None:
        logger.info("To'xtatish signali qabul qilindi.")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_stop)
        except NotImplementedError:
            # Windows kabi ba'zi platformalarda signal handler qo'llab-quvvatlanmasligi mumkin
            pass

    polling_task = asyncio.create_task(bot.polling(non_stop=True, skip_pending=True))

    await stop_event.wait()

    polling_task.cancel()
    scheduler.shutdown(wait=False)
    await db.close()
    logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
