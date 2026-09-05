"""Flood-protection middleware.

Belgilangan oyna ichida (``flood.window_seconds``) juda ko'p xabar yuborgan
foydalanuvchini vaqtincha (``flood.ban_seconds``) bloklaydi.

MUHIM: Adminlar bu tekshiruvdan ISTISNO qilinadi. Sabab: admin panelda
(masalan, bir vaqtning o'zida 100 ta video yuborib, 100 ta qism qo'shish)
qonuniy ravishda juda ko'p va tez-tez xabar yuborish talab qilinadi — flood
himoyasi bunday holatlarda adminning xabarlarini "spam" deb xato bloklab,
video/qismlar jimgina yo'qolib qolishiga sabab bo'lardi.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from container import Container


class FloodMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._timestamps: dict[int, deque[float]] = {}
        self._banned_until: dict[int, float] = {}

    async def _is_admin(self, container: Container, user_id: int) -> bool:
        if container.settings.is_admin(user_id):
            return True
        return await container.admins.is_admin(user_id)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: Container = data["container"]
        tg_user: TgUser | None = data.get("event_from_user")

        if tg_user is None:
            return await handler(event, data)

        if await self._is_admin(container, tg_user.id):
            return await handler(event, data)

        now = time.monotonic()
        flood_cfg = container.settings.flood

        banned_until = self._banned_until.get(tg_user.id)
        if banned_until and now < banned_until:
            return None  # jimgina e'tiborsiz qoldiramiz

        timestamps = self._timestamps.setdefault(tg_user.id, deque())
        timestamps.append(now)

        while timestamps and now - timestamps[0] > flood_cfg.window_seconds:
            timestamps.popleft()

        if len(timestamps) > flood_cfg.max_messages:
            self._banned_until[tg_user.id] = now + flood_cfg.ban_seconds
            timestamps.clear()
            return None

        return await handler(event, data)
