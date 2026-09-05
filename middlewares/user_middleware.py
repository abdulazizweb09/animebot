"""Har bir update uchun foydalanuvchini DB'dan yuklaydigan/yaratuvchi va
bloklangan foydalanuvchilarni to'xtatuvchi middleware.

Ishlagandan so'ng handlerlar ``db_user: User`` parametrini to'g'ridan-to'g'ri
qabul qilishi mumkin — qayta-qayta ``get_or_create`` chaqirish shart emas.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User as TgUser

from container import Container
from utils.i18n import t
from utils.logger import get_logger

logger = get_logger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: Container = data["container"]

        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        db_user, created = await container.user_service.get_or_create(
            user_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
        )
        data["db_user"] = db_user
        data["is_new_user"] = created

        if db_user.is_banned:
            text = t("banned", db_user.language, reason=db_user.ban_reason or "-")
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            return None

        return await handler(event, data)
