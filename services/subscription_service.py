"""Majburiy obuna kanallari bilan ishlash logikasi."""

from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from database.json_manager import JsonManager
from utils.logger import get_logger

logger = get_logger(__name__)

_NOT_MEMBER_STATUSES = {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}


class SubscriptionService:
    """``subscriptions.json`` — majburiy obuna kanallari ro'yxatini boshqaradi."""

    def __init__(self, manager: JsonManager) -> None:
        self._manager = manager

    async def list_channels(self, only_enabled: bool = True) -> list[dict]:
        channels = await self._manager.read("subscriptions.json", default=[])
        if only_enabled:
            channels = [c for c in channels if c.get("enabled", True)]
        return channels

    async def add_channel(
        self, channel_id: int, title: str, username: str | None, invite_link: str | None
    ) -> None:
        def _updater(data: list[dict]) -> list[dict]:
            data.append(
                {
                    "channel_id": channel_id,
                    "title": title,
                    "username": username,
                    "invite_link": invite_link,
                    "enabled": True,
                }
            )
            return data

        await self._manager.update("subscriptions.json", _updater, default=[])

    async def remove_channel(self, channel_id: int) -> bool:
        removed = False

        def _updater(data: list[dict]) -> list[dict]:
            nonlocal removed
            new_data = [c for c in data if c.get("channel_id") != channel_id]
            removed = len(new_data) != len(data)
            return new_data

        await self._manager.update("subscriptions.json", _updater, default=[])
        return removed

    async def check_user_subscribed_all(self, bot: Bot, user_id: int) -> tuple[bool, list[dict]]:
        """Foydalanuvchi barcha majburiy kanallarga obuna bo'lganmi tekshiradi.

        Qaytaradi: ``(hammasiga_obuna_bo'lganmi, obuna_bo'lmagan_kanallar)``
        """

        channels = await self.list_channels(only_enabled=True)
        if not channels:
            return True, []

        missing: list[dict] = []
        for channel in channels:
            channel_id = channel.get("channel_id")
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status in _NOT_MEMBER_STATUSES:
                    missing.append(channel)
            except TelegramBadRequest as exc:
                logger.warning(
                    "Kanal a'zoligini tekshirib bo'lmadi (channel_id=%s): %s",
                    channel_id,
                    exc,
                )
                # Bot kanalga admin bo'lmasa yoki kanal noto'g'ri — bloklamaymiz
                continue

        return (len(missing) == 0), missing
