"""
keyboards/user_keyboards.py
-----------------------------
Oddiy foydalanuvchilar uchun inline keyboardlar (minimal, chunki
foydalanuvchilar faqat hisobot yuborishi va eslatmalarga javob berishi
kerak).
"""

from __future__ import annotations

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def reminder_ack_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✍️ Hisobot yuborish", callback_data="user:report_start"))
    return kb
