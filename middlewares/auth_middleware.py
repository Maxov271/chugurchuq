"""
middlewares/auth_middleware.py
--------------------------------
Kirish huquqini tekshiruvchi yordamchi funksiya va dekoratorlar.
Botdan faqat administrator tomonidan oldindan ro'yxatga olingan
foydalanuvchilargina foydalana oladi; admin funksiyalari esa faqat
.env dagi ADMIN_IDS ro'yxatidagilarga ochiq.
"""

from __future__ import annotations

import functools
from typing import Awaitable, Callable

from config import settings
from database.queries import user_repo
from utils.logger import get_logger

logger = get_logger(__name__)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


async def is_registered_user(telegram_id: int) -> bool:
    user = await user_repo.get_by_telegram_id(telegram_id)
    return user is not None


def admin_only(handler: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
    """Faqat administratorlar uchun handlerni himoyalovchi dekorator."""

    @functools.wraps(handler)
    async def wrapper(message_or_call, *args, **kwargs):
        telegram_id = message_or_call.from_user.id
        if not is_admin(telegram_id):
            logger.warning("Ruxsatsiz admin urinishi: %s", telegram_id)
            return None
        return await handler(message_or_call, *args, **kwargs)

    return wrapper


def registered_user_only(handler: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
    """Faqat ro'yxatdan o'tgan (admin tomonidan qo'shilgan) foydalanuvchilar
    uchun handlerni himoyalovchi dekorator. Adminlar ham o'tadi."""

    @functools.wraps(handler)
    async def wrapper(message_or_call, *args, **kwargs):
        telegram_id = message_or_call.from_user.id
        if is_admin(telegram_id):
            return await handler(message_or_call, *args, **kwargs)
        if not await is_registered_user(telegram_id):
            logger.info("Ro'yxatdan o'tmagan foydalanuvchi murojaati: %s", telegram_id)
            return None
        return await handler(message_or_call, *args, **kwargs)

    return wrapper
