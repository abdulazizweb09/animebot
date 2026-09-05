"""🔔 Notification Center — foydalanuvchi bildirishnomalari."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_notifications")


@router.message(F.text.in_(all_variants("btn_notifications")))
async def show_notifications(message: Message, container: Container, db_user: User) -> None:
    unread = await container.notification_service.unread_count(db_user.user_id)
    notifications = await container.notification_service.list_for_user(db_user.user_id, limit=15)
    if not notifications:
        await message.answer(t("notifications_empty", db_user.language))
        return

    title = t("notifications_title", db_user.language)
    if unread:
        title += f" ({unread} ta o'qilmagan)"
    lines = [title]
    for n in notifications:
        mark = "🔵" if not n.is_read else "⚪️"
        ts = n.created_at[:16].replace("T", " ")
        lines.append(f"{mark} <b>{n.title}</b>\n{n.text}\n<i>{ts}</i>")

    rows = [[InlineKeyboardButton(text="✅ Barchasini o'qilgan deb belgilash", callback_data="notif:readall")]]
    await message.answer("\n\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "notif:readall")
async def mark_all_read(callback: CallbackQuery, container: Container, db_user: User) -> None:
    await container.notification_service.mark_all_read(db_user.user_id)
    await callback.answer(t("notifications_marked_read", db_user.language))
