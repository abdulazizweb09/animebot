"""``admins.json`` — runtime-da qo'shilgan adminlar ro'yxati."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.admin import AdminEntry
from database.repositories.base_repository import BaseRepository


class AdminRepository(BaseRepository[AdminEntry]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "admins.json", AdminEntry, id_field="admin_id")

    async def all_ids(self) -> list[int]:
        entries = await self.all()
        return [e.admin_id for e in entries]

    async def is_admin(self, admin_id: int) -> bool:
        """MUHIM: bu avtorizatsiya tekshiruvi bo'lgani uchun ataylab
        ``use_cache=False`` bilan chaqiriladi — TTL kesh eskirgan (stale)
        ma'lumot qaytarib, endigina o'chirilgan adminga hali ruxsat berib
        yuborishi yoki yangi qo'shilgan adminni darhol tanimay qolishi
        mumkin edi. Admin tekshiruvi kamdan-kam (faqat admin buyruqlarida)
        chaqirilgani uchun bu performance narxi ahamiyatsiz.
        """

        return await self.exists(admin_id, use_cache=False)
