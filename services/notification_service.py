"""In-bot bildirishnoma markazi (Notification Center)."""

from __future__ import annotations

import uuid

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from database.models.rating import Notification
from database.repositories.rating_repository import NotificationRepository
from database.repositories.user_repository import UserRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, notifications: NotificationRepository, users: UserRepository) -> None:
        self._notifications = notifications
        self._users = users

    async def create(
        self,
        user_id: int,
        kind: str,
        title: str,
        text: str,
        anime_code: str | None = None,
    ) -> Notification:
        notification = Notification(
            id=str(uuid.uuid4()), user_id=user_id, kind=kind, title=title, text=text,
            anime_code=anime_code,
        )
        await self._notifications.add(notification)
        return notification

    async def create_and_send(
        self,
        bot: Bot,
        user_id: int,
        kind: str,
        title: str,
        text: str,
        anime_code: str | None = None,
    ) -> Notification:
        """Bildirishnomani DOIM Notification Center'ga saqlaydi, lekin
        Telegram push-xabarini faqat foydalanuvchi "🔔 Bildirishnomalar"
        sozlamasini o'chirib qo'ymagan bo'lsa yuboradi (#Sozlamalar).
        """

        notification = await self.create(user_id, kind, title, text, anime_code)

        user = await self._users.get_by_id(user_id)
        if user is not None and not user.notifications_enabled:
            return notification

        try:
            await bot.send_message(user_id, f"🔔 <b>{title}</b>\n\n{text}")
        except TelegramForbiddenError:
            pass
        return notification

    async def list_for_user(self, user_id: int, limit: int = 20) -> list[Notification]:
        return await self._notifications.list_for_user(user_id, limit)

    async def unread_count(self, user_id: int) -> int:
        return await self._notifications.unread_count(user_id)

    async def mark_all_read(self, user_id: int) -> int:
        return await self._notifications.mark_all_read(user_id)
