"""Oddiy adminlar uchun granular ruxsatlarni boshqarish (permissions.json)."""

from __future__ import annotations

from config.enums import Permission
from config.settings import Settings
from database.json_manager import JsonManager


class PermissionService:
    def __init__(self, manager: JsonManager, settings: Settings) -> None:
        self._manager = manager
        self._settings = settings

    async def get_permissions(self, admin_id: int) -> list[str]:
        if self._settings.is_main_admin(admin_id):
            return [p.value for p in Permission.all()]

        # MUHIM: bu avtorizatsiya tekshiruvi — TTL kesh eskirgan ruxsatlar
        # ro'yxatini qaytarib, admin huquqi yangi berilgan/olib
        # tashlangandan keyin ham eski holatda ishlab qolmasligi uchun
        # ataylab ``use_cache=False`` bilan o'qiladi.
        data = await self._manager.read("permissions.json", default={}, use_cache=False)
        return data.get(str(admin_id), [])

    async def has_permission(self, admin_id: int, permission: Permission) -> bool:
        if self._settings.is_main_admin(admin_id):
            return True
        perms = await self.get_permissions(admin_id)
        return permission.value in perms

    async def set_permissions(self, admin_id: int, permissions: list[Permission]) -> None:
        def _updater(data: dict) -> dict:
            data[str(admin_id)] = [p.value for p in permissions]
            return data

        await self._manager.update("permissions.json", _updater, default={})

    async def grant(self, admin_id: int, permission: Permission) -> None:
        def _updater(data: dict) -> dict:
            current = set(data.get(str(admin_id), []))
            current.add(permission.value)
            data[str(admin_id)] = sorted(current)
            return data

        await self._manager.update("permissions.json", _updater, default={})

    async def revoke(self, admin_id: int, permission: Permission) -> None:
        def _updater(data: dict) -> dict:
            current = set(data.get(str(admin_id), []))
            current.discard(permission.value)
            data[str(admin_id)] = sorted(current)
            return data

        await self._manager.update("permissions.json", _updater, default={})

    async def remove_admin(self, admin_id: int) -> None:
        def _updater(data: dict) -> dict:
            data.pop(str(admin_id), None)
            return data

        await self._manager.update("permissions.json", _updater, default={})
