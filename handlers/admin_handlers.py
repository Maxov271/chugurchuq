"""
handlers/admin_handlers.py
-----------------------------
Administrator paneli bilan bog'liq barcha handlerlar: asosiy menyu,
hisobotlar, foydalanuvchilar, jadval (eslatma) belgilash, statistika,
eksport, backup, sozlamalar va qidiruv.
"""

from __future__ import annotations

import math

from telebot.async_telebot import AsyncTeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import CallbackQuery, Message

from config import settings
from database.queries import (
    activity_repo,
    message_repo,
    schedule_repo,
    user_repo,
)
from keyboards.admin_keyboards import (
    back_button,
    backup_menu,
    confirm_keyboard,
    export_filter_keyboard,
    export_menu,
    main_menu,
    settings_menu,
    statistics_menu,
    user_detail_keyboard,
    user_list_keyboard,
    users_menu,
    weekday_keyboard,
)
from middlewares.auth_middleware import admin_only
from services.backup_service import backup_service
from services.export_service import export_service
from services.statistics_service import statistics_service
from services.user_service import user_service
from states.admin_states import AdminState, state_manager
from utils.logger import get_logger

logger = get_logger(__name__)

USERS_PAGE_SIZE = 8
WEEKDAY_NAMES = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


async def send_main_menu(bot: AsyncTeleBot, chat_id: int) -> None:
    overview = await statistics_service.overview()
    text = (
        "🛠 <b>Administrator paneli</b>\n\n"
        f"👥 Jami foydalanuvchilar: {overview['total_users']}\n"
        f"📅 Bugungi hisobotlar: {overview['today_reports']}\n"
        f"🔕 O'qilmagan: {overview['unread']}\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await bot.send_message(chat_id, text, reply_markup=main_menu(), parse_mode="HTML")


def _format_report_line(row) -> str:
    read_mark = "✅" if row["is_read"] else "🔕"
    return f"{read_mark} <code>{row['internal_id']}</code> — {row['report_date']} {row['report_time']} — {row['media_type']} content={row['content']}"


async def _render_report_list(bot: AsyncTeleBot, chat_id: int, message_id: int | None, rows, title: str) -> None:
    if not rows:
        text = f"<b>{title}</b>\n\nHozircha yozuvlar mavjud emas."
    else:
        lines = [_format_report_line(r) for r in rows[:25]]
        extra = f"\n\n... va yana {len(rows) - 25} ta" if len(rows) > 25 else ""
        text = f"<b>{title}</b> (jami: {len(rows)})\n\n" + "\n".join(lines) + extra

    if message_id:
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button(), parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text, reply_markup=back_button(), parse_mode="HTML")


def register_admin_handlers(bot: AsyncTeleBot) -> None:

    @bot.message_handler(commands=["menu", "admin"])
    @admin_only
    async def menu_command(message: Message) -> None:
        state_manager.clear(message.from_user.id)
        await send_main_menu(bot, message.chat.id)

    # ------------------------------------------------------------------ #
    # Asosiy callback dispatcher
    # ------------------------------------------------------------------ #
    @bot.callback_query_handler(func=lambda c: True)
    @admin_only
    async def callback_dispatcher(call: CallbackQuery) -> None:
        data = call.data
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        admin_id = call.from_user.id

        try:
            if data == "noop":
                await bot.answer_callback_query(call.id)
                return

            if data == "menu:main":
                state_manager.clear(admin_id)
                await bot.answer_callback_query(call.id)
                overview = await statistics_service.overview()
                text = (
                    "🛠 <b>Administrator paneli</b>\n\n"
                    f"👥 Jami foydalanuvchilar: {overview['total_users']}\n"
                    f"📅 Bugungi hisobotlar: {overview['today_reports']}\n"
                    f"🔕 O'qilmagan: {overview['unread']}\n\n"
                    "Quyidagi bo'limlardan birini tanlang:"
                )
                await bot.edit_message_text(text, chat_id, message_id, reply_markup=main_menu(), parse_mode="HTML")
                return

            parts = data.split(":")
            namespace = parts[0]

            # ---------------- Hisobotlar ----------------
            if namespace == "rep":
                await bot.answer_callback_query(call.id)
                kind = parts[1]
                if kind == "today":
                    rows = await message_repo.get_today()
                    await _render_report_list(bot, chat_id, message_id, rows, "📅 Bugungi hisobotlar")
                elif kind == "weekly":
                    rows = await message_repo.get_weekly()
                    await _render_report_list(bot, chat_id, message_id, rows, "🗓 Haftalik hisobotlar")
                elif kind == "monthly":
                    rows = await message_repo.get_monthly()
                    await _render_report_list(bot, chat_id, message_id, rows, "📆 Oylik hisobotlar")
                elif kind == "all":
                    rows = await message_repo.get_all()
                    await _render_report_list(bot, chat_id, message_id, rows, "📚 Barcha hisobotlar")
                elif kind == "unread":
                    rows = await message_repo.get_unread()
                    await _render_report_list(bot, chat_id, message_id, rows, "🔕 O'qilmagan hisobotlar")
                elif kind == "low_activity":
                    rows = await user_repo.inactive_since(30)
                    lines = [f"<code>{u['internal_id']}</code> — {u['full_name'] or u['username'] or u['telegram_id']}" for u in rows]
                    text = "📉 <b>Faolligi past foydalanuvchilar</b>\n\n" + ("\n".join(lines) if lines else "Mavjud emas.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button(), parse_mode="HTML")
                return

            # ---------------- Statistika ----------------
            if namespace == "stat":
                await bot.answer_callback_query(call.id)
                if parts[1] == "menu":
                    await bot.edit_message_text("📊 <b>Statistikalar</b>", chat_id, message_id, reply_markup=statistics_menu(), parse_mode="HTML")
                elif parts[1] == "top_active":
                    rows = await statistics_service.top_active(10)
                    lines = [f"{i+1}. <code>{u['internal_id']}</code> — {u['total_reports']} ta hisobot" for i, u in enumerate(rows)]
                    text = "🏆 <b>TOP 10 faol foydalanuvchilar</b>\n\n" + ("\n".join(lines) if lines else "Ma'lumot yo'q.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button("stat:menu"), parse_mode="HTML")
                elif parts[1] == "top_inactive":
                    rows = await statistics_service.top_inactive(10)
                    lines = [f"{i+1}. <code>{u['internal_id']}</code> — {u['total_reports']} ta hisobot" for i, u in enumerate(rows)]
                    text = "💤 <b>TOP 10 sust foydalanuvchilar</b>\n\n" + ("\n".join(lines) if lines else "Ma'lumot yo'q.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button("stat:menu"), parse_mode="HTML")
                elif parts[1] == "inactive":
                    days = int(parts[2])
                    rows = await statistics_service.inactive_for_days(days)
                    lines = [f"<code>{u['internal_id']}</code> — oxirgi faollik: {u['last_activity'] or 'hech qachon'}" for u in rows]
                    text = f"⏳ <b>{days} kundan beri faollik yo'q</b>\n\n" + ("\n".join(lines) if lines else "Mavjud emas.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button("stat:menu"), parse_mode="HTML")
                return

            # ---------------- Foydalanuvchilar ----------------
            if namespace == "users":
                action = parts[1]
                if action == "menu":
                    await bot.answer_callback_query(call.id)
                    await bot.edit_message_text("👥 <b>Foydalanuvchilar</b>", chat_id, message_id, reply_markup=users_menu(), parse_mode="HTML")
                elif action == "add":
                    await bot.answer_callback_query(call.id)
                    state_manager.set_state(admin_id, AdminState.ADD_USER_WAIT_CONTACT)
                    await bot.edit_message_text(
                        "➕ <b>Yangi foydalanuvchi qo'shish</b>\n\n"
                        "Foydalanuvchining kontaktini forward qiling yoki quyidagi formatda yuboring:\n"
                        "<code>telegram_id;Ism Familiya</code>",
                        chat_id, message_id, reply_markup=back_button("users:menu"), parse_mode="HTML",
                    )
                elif action == "list":
                    await bot.answer_callback_query(call.id)
                    page = int(parts[2])
                    all_users = await user_repo.get_all()
                    total_pages = max(math.ceil(len(all_users) / USERS_PAGE_SIZE), 1)
                    page_users = all_users[page * USERS_PAGE_SIZE:(page + 1) * USERS_PAGE_SIZE]
                    text = f"📋 <b>Foydalanuvchilar ro'yxati</b> (jami: {len(all_users)})"
                    await bot.edit_message_text(
                        text, chat_id, message_id,
                        reply_markup=user_list_keyboard(page_users, page, total_pages), parse_mode="HTML",
                    )
                elif action == "detail":
                    await bot.answer_callback_query(call.id)
                    user_id = int(parts[2])
                    user = await user_repo.get_by_id(user_id)
                    reports_count = await message_repo.count_by_user(user_id)
                    username_line = f"Username: @{user['username']}\n" if user['username'] else ""
                    text = (
                        f"👤 <b>{user['internal_id']}</b>\n"
                        f"Ism: {user['full_name'] or '—'}\n"
                        f"{username_line}"
                    )
                    text += (
                        f"Status: {user['status']}\n"
                        f"Ro'yxatga olingan: {user['registered_at']}\n"
                        f"Oxirgi faollik: {user['last_activity'] or 'hech qachon'}\n"
                        f"Jami hisobotlar: {reports_count}\n"
                    )
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=user_detail_keyboard(user_id), parse_mode="HTML")
                elif action == "activity":
                    await bot.answer_callback_query(call.id)
                    user_id = int(parts[2])
                    rows = await activity_repo.get_by_user(user_id, limit=20)
                    lines = [f"{r['created_at']} — {r['action']} {r['details'] or ''}" for r in rows]
                    text = "📈 <b>Faollik tarixi</b>\n\n" + ("\n".join(lines) if lines else "Mavjud emas.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button(f"users:detail:{user_id}"), parse_mode="HTML")
                elif action == "delete":
                    await bot.answer_callback_query(call.id)
                    user_id = int(parts[2])
                    await bot.edit_message_text(
                        "❗️ Foydalanuvchini o'chirmoqchimisiz?", chat_id, message_id,
                        reply_markup=confirm_keyboard("delete_user", user_id),
                    )
                elif action == "attention":
                    await bot.answer_callback_query(call.id)
                    entries = await user_service.build_attention_list()
                    if not entries:
                        text = "✅ E'tibor talab qiluvchi foydalanuvchilar yo'q."
                    else:
                        blocks = []
                        for e in entries[:20]:
                            blocks.append(
                                f"<code>{e.internal_id}</code>\n"
                                f"• {e.reason}\n"
                                f"• eslatmalar: {e.reminders_sent} ta\n"
                                f"• oxirgi faollik: {e.last_activity or 'hech qachon'}\n"
                                f"• jami hisobotlar: {e.total_replies} ta"
                            )
                        text = "⚠️ <b>E'tibor talab qiluvchi foydalanuvchilar</b>\n\n" + "\n\n".join(blocks)
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button("users:menu"), parse_mode="HTML")
                return

            # ---------------- Tasdiqlash ----------------
            if namespace == "confirm":
                action, target_id = parts[1], int(parts[2])
                await bot.answer_callback_query(call.id, "Bajarildi")
                if action == "delete_user":
                    await user_repo.soft_delete(target_id)
                    await bot.edit_message_text("🗑 Foydalanuvchi o'chirildi.", chat_id, message_id, reply_markup=back_button("users:menu"))
                return

            # ---------------- Jadval / Eslatma ----------------
            if namespace == "sched":
                action = parts[1]
                if action == "add":
                    await bot.answer_callback_query(call.id)
                    user_id = int(parts[2])
                    await bot.edit_message_text(
                        "📅 Hafta kunini tanlang:", chat_id, message_id, reply_markup=weekday_keyboard(user_id),
                    )
                elif action == "weekday":
                    await bot.answer_callback_query(call.id)
                    user_id, weekday = int(parts[2]), int(parts[3])
                    state_manager.set_state(admin_id, AdminState.SCHEDULE_WAIT_TIME)
                    state_manager.set_data(admin_id, "sched_user_id", user_id)
                    state_manager.set_data(admin_id, "sched_weekday", weekday)
                    await bot.edit_message_text(
                        f"🕒 {WEEKDAY_NAMES[weekday]} kuni uchun vaqtni kiriting (masalan: 08:00):",
                        chat_id, message_id, reply_markup=back_button(f"users:detail:{user_id}"),
                    )
                elif action == "list":
                    await bot.answer_callback_query(call.id)
                    user_id = int(parts[2])
                    rows = await schedule_repo.get_by_user(user_id)
                    lines = [f"{WEEKDAY_NAMES[r['weekday']]} {r['time']} — {r['reminder_text']}" for r in rows]
                    text = "📋 <b>Jadvallar</b>\n\n" + ("\n".join(lines) if lines else "Jadval mavjud emas.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button(f"users:detail:{user_id}"), parse_mode="HTML")
                return

            # ---------------- Sozlamalar ----------------
            if namespace == "settings":
                await bot.answer_callback_query(call.id)
                if parts[1] == "menu":
                    await bot.edit_message_text("⚙️ <b>Sozlamalar</b>", chat_id, message_id, reply_markup=settings_menu(), parse_mode="HTML")
                elif parts[1] == "reminders":
                    await bot.edit_message_text(
                        "🔔 Eslatma matnlari har bir foydalanuvchi uchun jadval belgilashda "
                        "alohida kiritiladi (Foydalanuvchilar → foydalanuvchi → Jadval belgilash).",
                        chat_id, message_id, reply_markup=back_button("settings:menu"),
                    )
                return

            # ---------------- Backup ----------------
            if namespace == "backup":
                if parts[1] == "menu":
                    await bot.answer_callback_query(call.id)
                    await bot.edit_message_text("💾 <b>Backup</b>", chat_id, message_id, reply_markup=backup_menu(), parse_mode="HTML")
                elif parts[1] == "run":
                    await bot.answer_callback_query(call.id, "Backup boshlandi...")
                    paths = await backup_service.run_full_backup()
                    text = "✅ Backup yakunlandi:\n" + "\n".join(f"• {k}: {v.name}" for k, v in paths.items())
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button("backup:menu"))
                elif parts[1] == "history":
                    await bot.answer_callback_query(call.id)
                    from database.queries import backup_repo
                    rows = await backup_repo.history(15)
                    lines = [f"{r['created_at']} — {r['backup_type']} — {r['status']}" for r in rows]
                    text = "📜 <b>Backup tarixi</b>\n\n" + ("\n".join(lines) if lines else "Mavjud emas.")
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=back_button("backup:menu"), parse_mode="HTML")
                return

            # ---------------- Eksport ----------------
            if namespace == "export":
                action = parts[1]
                if action == "menu":
                    await bot.answer_callback_query(call.id)
                    await bot.edit_message_text("📤 <b>Eksport formatini tanlang</b>", chat_id, message_id, reply_markup=export_menu(), parse_mode="HTML")
                elif action in ("txt", "csv", "xlsx", "pdf"):
                    await bot.answer_callback_query(call.id)
                    await bot.edit_message_text(
                        f"📤 <b>{action.upper()}</b> — filtrni tanlang:", chat_id, message_id,
                        reply_markup=export_filter_keyboard(action), parse_mode="HTML",
                    )
                elif action == "do":
                    export_type, filter_type = parts[2], parts[3]
                    await bot.answer_callback_query(call.id, "Tayyorlanmoqda...")
                    method = getattr(export_service, f"export_{export_type}")
                    path = await method(filter_type, admin_id)
                    with open(path, "rb") as f:
                        await bot.send_document(chat_id, f, caption=f"📤 Eksport: {export_type.upper()} ({filter_type})")
                return

            # ---------------- Qidiruv ----------------
            if namespace == "search":
                if parts[1] == "start":
                    await bot.answer_callback_query(call.id)
                    state_manager.set_state(admin_id, AdminState.SEARCH_WAIT_QUERY)
                    await bot.edit_message_text(
                        "🔍 Qidiruv so'zini kiriting (ism, username yoki ID):",
                        chat_id, message_id, reply_markup=back_button(),
                    )
                return

            # ---------------- Xabar (hisobot) amallari ----------------
            if namespace == "msg":
                action = parts[1]
                target_message_id = int(parts[2])
                if action == "read":
                    await message_repo.mark_read(target_message_id)
                    await bot.answer_callback_query(call.id, "O'qilgan deb belgilandi ✅")
                    try:
                        await bot.delete_message(chat_id, message_id)
                    except ApiTelegramException as exc:
                        logger.debug("Xabarni o'chirib bo'lmadi: %s", exc)
                elif action == "reply":
                    await bot.answer_callback_query(call.id)
                    state_manager.set_state(admin_id, AdminState.BROADCAST_WAIT_TEXT)
                    state_manager.set_data(admin_id, "reply_to_message_id", target_message_id)
                    await bot.send_message(chat_id, "↩️ Javob matnini kiriting:")
                return

        except ApiTelegramException as exc:
            logger.error("Callback xatosi (%s): %s", data, exc)
            await bot.answer_callback_query(call.id, "Xatolik yuz berdi.")


# ========================================================================
# ADMIN FSM (ko'p bosqichli) matn kiritishlarini qayta ishlash
# ========================================================================
async def handle_admin_fsm_input(bot: AsyncTeleBot, message: Message) -> None:
    admin_id = message.from_user.id
    state = state_manager.get_state(admin_id)

    if state == AdminState.ADD_USER_WAIT_CONTACT:
        telegram_id = None
        full_name = None
        username = None

        if message.content_type == "contact":
            telegram_id = message.contact.user_id
            full_name = f"{message.contact.first_name or ''} {message.contact.last_name or ''}".strip()
        elif message.forward_from:
            telegram_id = message.forward_from.id
            full_name = message.forward_from.full_name
            username = message.forward_from.username
        elif message.content_type == "text" and ";" in message.text:
            raw_id, _, name = message.text.partition(";")
            if raw_id.strip().isdigit():
                telegram_id = int(raw_id.strip())
                full_name = name.strip()

        if telegram_id is None:
            await bot.send_message(message.chat.id, "⚠️ Noto'g'ri format. Qaytadan urinib ko'ring.")
            return

        user = await user_service.register_user(telegram_id, full_name or "Noma'lum", username)
        state_manager.clear(admin_id)
        await bot.send_message(
            message.chat.id,
            f"✅ Foydalanuvchi qo'shildi: <code>{user['internal_id']}</code>",
            reply_markup=back_button("users:menu"),
            parse_mode="HTML",
        )
        return

    if state == AdminState.SCHEDULE_WAIT_TIME:
        if message.content_type != "text":
            await bot.send_message(message.chat.id, "⚠️ Vaqtni matn ko'rinishida kiriting (masalan 08:00).")
            return
        time_str = message.text.strip()
        if len(time_str) != 5 or time_str[2] != ":":
            await bot.send_message(message.chat.id, "⚠️ Format noto'g'ri. Masalan: 08:00")
            return
        state_manager.set_data(admin_id, "sched_time", time_str)
        state_manager.set_state(admin_id, AdminState.SCHEDULE_WAIT_TEXT)
        await bot.send_message(message.chat.id, "✍️ Eslatma matnini kiriting:")
        return

    if state == AdminState.SCHEDULE_WAIT_TEXT:
        if message.content_type != "text":
            await bot.send_message(message.chat.id, "⚠️ Matn kiriting.")
            return
        user_id = state_manager.get_data(admin_id, "sched_user_id")
        weekday = state_manager.get_data(admin_id, "sched_weekday")
        time_str = state_manager.get_data(admin_id, "sched_time")
        await schedule_repo.add(user_id, weekday, time_str, message.text.strip())
        state_manager.clear(admin_id)
        await bot.send_message(
            message.chat.id,
            f"✅ Jadval qo'shildi: {WEEKDAY_NAMES[weekday]} {time_str}",
            reply_markup=back_button(f"users:detail:{user_id}"),
        )
        return

    if state == AdminState.SEARCH_WAIT_QUERY:
        if message.content_type != "text":
            return
        results = await user_repo.search(message.text.strip())
        state_manager.clear(admin_id)
        if not results:
            await bot.send_message(message.chat.id, "🔍 Hech narsa topilmadi.", reply_markup=back_button())
            return
        page_users = results[:USERS_PAGE_SIZE]
        total_pages = max(math.ceil(len(results) / USERS_PAGE_SIZE), 1)
        await bot.send_message(
            message.chat.id,
            f"🔍 Qidiruv natijalari (jami: {len(results)})",
            reply_markup=user_list_keyboard(page_users, 0, total_pages),
        )
        return

    if state == AdminState.BROADCAST_WAIT_TEXT:
        if message.content_type != "text":
            await bot.send_message(message.chat.id, "⚠️ Matn kiriting.")
            return
        target_message_id = state_manager.get_data(admin_id, "reply_to_message_id")
        original = await message_repo.get_by_id(target_message_id)
        state_manager.clear(admin_id)
        if original:
            try:
                await bot.send_message(original["telegram_id"], f"💬 <b>Admin javobi:</b>\n\n{message.text}", parse_mode="HTML")
                await message_repo.mark_replied(target_message_id)
                await bot.send_message(message.chat.id, "✅ Javob yuborildi.")
            except ApiTelegramException as exc:
                logger.error("Javob yuborilmadi: %s", exc)
                await bot.send_message(message.chat.id, "❌ Javob yuborilmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).")
        return
