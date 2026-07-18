"""
handlers/user_handlers.py
----------------------------
Oddiy foydalanuvchilar bilan bog'liq barcha handlerlar:
  * /start buyrug'i;
  * matn/rasm/video/audio/voice/hujjat/location/contact ko'rinishidagi
    hisobotlarni qabul qilish;
  * eslatmadagi "Hisobot yuborish" tugmasi.

Eslatma: bitta konsolidatsiyalangan content handler orqali ADMIN uchun
FSM (ko'p bosqichli) kiritishlar ham shu yerdan admin_handlers modulidagi
`handle_admin_fsm_input` funksiyasiga uzatiladi — bu ikkita alohida
handlerning bir xil content_type uchun to'qnashib ketishining oldini oladi.
"""

from __future__ import annotations

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, Message

from database.queries import user_repo
from middlewares.auth_middleware import is_admin
from services.reminder_service import last_reminder_message
from services.report_service import report_service
from services.user_service import user_service
from states.admin_states import AdminState, state_manager
from utils.logger import get_logger

logger = get_logger(__name__)

ALL_CONTENT_TYPES = [
    "text", "photo", "video", "audio", "voice", "document", "location", "contact",
]


def register_user_handlers(bot: AsyncTeleBot) -> None:

    @bot.message_handler(commands=["start"])
    async def start_handler(message: Message) -> None:
        telegram_id = message.from_user.id

        if is_admin(telegram_id):
            from handlers.admin_handlers import send_main_menu
            await send_main_menu(bot, message.chat.id)
            return

        user = await user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            await bot.send_message(
                message.chat.id,
                "🚫 Kechirasiz, siz botdan foydalanish huquqiga ega emassiz.\n"
                "Administrator sizni ro'yxatga olgandan so'ng foydalanishingiz mumkin bo'ladi.",
            )
            return

        await user_service.touch_activity(user)
        await bot.send_message(
            message.chat.id,
            f"👋 Assalomu alaykum, {user['full_name'] or 'foydalanuvchi'}!\n\n"
            "Belgilangan vaqtda sizga eslatma yuboriladi. Eslatma kelganda "
            "hisobotingizni (matn, rasm, video, audio, hujjat va h.k.) shu chatga yuboring.",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "user:report_start")
    async def report_start_callback(call: CallbackQuery) -> None:
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, "✍️ Hisobotingizni yuboring:")

    @bot.message_handler(content_types=ALL_CONTENT_TYPES)
    async def content_dispatcher(message: Message) -> None:
        telegram_id = message.from_user.id

        # 1) Admin ko'p bosqichli (FSM) kiritish jarayonida bo'lsa
        if is_admin(telegram_id):
            if state_manager.get_state(telegram_id) != AdminState.NONE:
                from handlers.admin_handlers import handle_admin_fsm_input
                await handle_admin_fsm_input(bot, message)
            # Admin FSM holatida bo'lmasa — hisobot sifatida qabul qilinmaydi
            return

        # 2) Ro'yxatdan o'tgan oddiy foydalanuvchi — hisobot sifatida qabul qilinadi
        user = await user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            await bot.send_message(
                message.chat.id, "🚫 Siz botdan foydalanish huquqiga ega emassiz."
            )
            return

        await user_service.touch_activity(user)
        last_reminder_id = last_reminder_message.pop(telegram_id, None)
        await report_service.handle_incoming_report(bot, message, user, last_reminder_id)
        await bot.send_message(message.chat.id, "✅ Hisobotingiz qabul qilindi. Rahmat!")
