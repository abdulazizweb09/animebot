"""Admin/main-admin ekanligini tekshiruvchi filterlar.

Admin ikki manbadan aniqlanadi:
    1. ``.env`` dagi statik ``MAIN_ADMIN_IDS`` / ``ADMIN_IDS``
    2. Runtime-da bot orqali qo'shilgan ``admins.json`` (faqat main-admin
       tomonidan boshqariladi)
"""

from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, User as TgUser

from container import Container


class IsMainAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, **data: Any) -> bool:
        container: Container = data["container"]
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None:
            return False
        return container.settings.is_main_admin(tg_user.id)


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, **data: Any) -> bool:
        container: Container = data["container"]
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None:
            return False
        if container.settings.is_admin(tg_user.id):
            return True
        return await container.admins.is_admin(tg_user.id)
