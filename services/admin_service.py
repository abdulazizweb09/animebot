"""Adminlarni qo'shish/olib tashlash logikasi (main-admin uchun)."""

from __future__ import annotations

from config.enums import LogAction, UserRole
from database.json_manager import JsonManager
from database.models.admin import AdminEntry
from database.repositories.admin_repository import AdminRepository
from database.repositories.user_repository import UserRepository
from services.audit_log_service import AuditLogService
from services.permission_service import PermissionService


class AdminService:
    def __init__(
        self,
        admins: AdminRepository,
        users: UserRepository,
        permissions: PermissionService,
        audit: AuditLogService,
        manager: JsonManager,
    ) -> None:
        self._admins = admins
        self._users = users
        self._permissions = permissions
        self._audit = audit
        self._manager = manager

    async def add_admin(self, admin_id: int, added_by: int) -> bool:
        _saved, added = await self._admins.add_if_absent(
            AdminEntry(admin_id=admin_id, added_by=added_by)
        )
        if not added:
            return False

        user = await self._users.get_by_id(admin_id)
        if user:
            await self._users.set_role(admin_id, UserRole.ADMIN.value)

        # Qo'shimcha ehtiyot chorasi: admins.json/users.json JsonManager
        # tomonidan har bir yozishdan keyin avtomatik qayta-keshlanadi, lekin
        # IsAdmin filteri KEYINGI update'da eng yangi holatni ko'rishini
        # 100% kafolatlash uchun keshni bu yerda ham qo'lda tozalaymiz.
        self._manager.cache_clear("admins.json")
        self._manager.cache_clear("users.json")

        await self._audit.log(added_by, LogAction.ADMIN_ADD, {"target": admin_id})
        return True

    async def remove_admin(self, admin_id: int, removed_by: int) -> bool:
        removed = await self._admins.hard_delete(admin_id)
        if removed:
            await self._permissions.remove_admin(admin_id)
            user = await self._users.get_by_id(admin_id)
            if user:
                await self._users.set_role(admin_id, UserRole.USER.value)

            self._manager.cache_clear("admins.json")
            self._manager.cache_clear("permissions.json")
            self._manager.cache_clear("users.json")

            await self._audit.log(removed_by, LogAction.ADMIN_REMOVE, {"target": admin_id})
        return removed

    async def list_admins(self) -> list[int]:
        return await self._admins.all_ids()
