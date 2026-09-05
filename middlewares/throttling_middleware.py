"""Oddiy per-user throttling middleware.

VIP foydalanuvchilar tezroq (``rate_limit.vip_seconds``), oddiylar sekinroq
(``rate_limit.default_seconds``) oraliqda so'rov yubora oladi.

Adminlar bu tekshiruvdan ISTISNO — admin panelda ketma-ket ko'p fayl
(masalan, bir nechta video) yuborish qonuniy ish oqimi, uni sekinlashtirish
kerak emas.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from container import Container


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._last_call: dict[int, float] = {}

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
        last = self._last_call.get(tg_user.id, 0.0)

        vip = await container.vips.get_active_for_user(tg_user.id)
        limit = (
            container.settings.rate_limit.vip_seconds
            if vip
            else container.settings.rate_limit.default_seconds
        )

        if now - last < limit:
            # Juda tez-tez so'rov — jimgina e'tiborsiz qoldiramiz
            return None

        self._last_call[tg_user.id] = now
        return await handler(event, data)
