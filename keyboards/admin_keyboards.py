"""
keyboards/admin_keyboards.py
-----------------------------
Administrator paneli uchun barcha Inline Keyboard'lar. Callback data
formati: "namespace:action:param" ko'rinishida, handlerlarda oson
parse qilish uchun.
"""

from __future__ import annotations

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📅 Bugungi hisobotlar", callback_data="rep:today"),
        InlineKeyboardButton("🗓 Haftalik hisobotlar", callback_data="rep:weekly"),
    )
    kb.add(
        InlineKeyboardButton("📆 Oylik hisobotlar", callback_data="rep:monthly"),
        InlineKeyboardButton("📚 Barcha hisobotlar", callback_data="rep:all"),
    )
    kb.add(
        InlineKeyboardButton("🔕 O'qilmagan hisobotlar", callback_data="rep:unread"),
        InlineKeyboardButton("📉 Faolligi past", callback_data="rep:low_activity"),
    )
    kb.add(
        InlineKeyboardButton("🏆 TOP 10 faol", callback_data="stat:top_active"),
        InlineKeyboardButton("💤 TOP 10 sust", callback_data="stat:top_inactive"),
    )
    kb.add(
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="users:menu"),
        InlineKeyboardButton("📊 Statistikalar", callback_data="stat:menu"),
    )
    kb.add(
        InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings:menu"),
        InlineKeyboardButton("💾 Backup", callback_data="backup:menu"),
    )
    kb.add(
        InlineKeyboardButton("📤 Eksport", callback_data="export:menu"),
        InlineKeyboardButton("🔍 Qidiruv", callback_data="search:start"),
    )
    return kb


def back_button(callback_data: str = "menu:main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=callback_data))
    return kb


def users_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Foydalanuvchi qo'shish", callback_data="users:add"),
        InlineKeyboardButton("📋 Ro'yxat", callback_data="users:list:0"),
    )
    kb.add(InlineKeyboardButton("⚠️ E'tibor talab qiluvchilar", callback_data="users:attention"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:main"))
    return kb


def user_list_keyboard(users: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for u in users:
        label = f"{u['internal_id']} — {u['full_name'] or u['username'] or u['telegram_id']} ({u['status']})"
        kb.add(InlineKeyboardButton(label, callback_data=f"users:detail:{u['id']}"))

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"users:list:{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{max(total_pages, 1)}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"users:list:{page + 1}"))
    if nav_row:
        kb.row(*nav_row)
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="users:menu"))
    return kb


def user_detail_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📅 Jadval belgilash", callback_data=f"sched:add:{user_id}"),
        InlineKeyboardButton("📋 Jadvallar", callback_data=f"sched:list:{user_id}"),
    )
    kb.add(
        InlineKeyboardButton("📈 Faollik tarixi", callback_data=f"users:activity:{user_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"users:delete:{user_id}"),
    )
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="users:list:0"))
    return kb


def confirm_keyboard(action: str, target_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"confirm:{action}:{target_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data="menu:main"),
    )
    return kb


def weekday_keyboard(user_id: int) -> InlineKeyboardMarkup:
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    kb = InlineKeyboardMarkup(row_width=2)
    for i, day in enumerate(days):
        kb.add(InlineKeyboardButton(day, callback_data=f"sched:weekday:{user_id}:{i}"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=f"users:detail:{user_id}"))
    return kb


def statistics_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏆 TOP 10 faol", callback_data="stat:top_active"),
        InlineKeyboardButton("💤 TOP 10 sust", callback_data="stat:top_inactive"),
    )
    kb.add(
        InlineKeyboardButton("1 kun faolsiz", callback_data="stat:inactive:1"),
        InlineKeyboardButton("7 kun faolsiz", callback_data="stat:inactive:7"),
    )
    kb.add(
        InlineKeyboardButton("30 kun faolsiz", callback_data="stat:inactive:30"),
        InlineKeyboardButton("90 kun faolsiz", callback_data="stat:inactive:90"),
    )
    kb.add(InlineKeyboardButton("180 kun faolsiz", callback_data="stat:inactive:180"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:main"))
    return kb


def export_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📄 TXT", callback_data="export:txt"),
        InlineKeyboardButton("📊 CSV", callback_data="export:csv"),
    )
    kb.add(
        InlineKeyboardButton("📗 XLSX", callback_data="export:xlsx"),
        InlineKeyboardButton("📕 PDF", callback_data="export:pdf"),
    )
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:main"))
    return kb


def backup_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💾 Hozir backup olish", callback_data="backup:run"))
    kb.add(InlineKeyboardButton("📜 Backup tarixi", callback_data="backup:history"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:main"))
    return kb


def settings_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔔 Eslatma sozlamalari", callback_data="settings:reminders"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:main"))
    return kb


def export_filter_keyboard(export_type: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Bugungi", callback_data=f"export:do:{export_type}:today"),
        InlineKeyboardButton("Haftalik", callback_data=f"export:do:{export_type}:weekly"),
    )
    kb.add(
        InlineKeyboardButton("Oylik", callback_data=f"export:do:{export_type}:monthly"),
        InlineKeyboardButton("Hammasi", callback_data=f"export:do:{export_type}:all"),
    )
    kb.add(InlineKeyboardButton("O'qilmaganlar", callback_data=f"export:do:{export_type}:unread"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="export:menu"))
    return kb


def report_item_keyboard(message_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ O'qildi", callback_data=f"msg:read:{message_id}"),
        InlineKeyboardButton("↩️ Javob berish", callback_data=f"msg:reply:{message_id}"),
    )
    return kb
