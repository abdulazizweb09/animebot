"""``vip.json`` bilan ishlaydigan repository."""

from __future__ import annotations

from datetime import datetime, timezone

from database.json_manager import JsonManager
from database.models.vip import VipSubscription
from database.repositories.base_repository import BaseRepository


class VipRepository(BaseRepository[VipSubscription]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "vip.json", VipSubscription, id_field="id")

    async def get_active_for_user(self, user_id: int) -> VipSubscription | None:
        subs = await self.find_all(lambda s: s.get("user_id") == user_id)
        active = [s for s in subs if s.is_active()]
        if not active:
            return None
        return max(active, key=lambda s: s.expires_at or "")

    async def get_pending_for_user(self, user_id: int) -> VipSubscription | None:
        return await self.find_one(
            lambda s: s.get("user_id") == user_id and s.get("status") == "pending"
        )

    async def list_pending(self) -> list[VipSubscription]:
        return await self.find_all(lambda s: s.get("status") == "pending")

    async def list_expiring_within(self, days: int) -> list[VipSubscription]:
        subs = await self.all()
        now = datetime.now(timezone.utc)
        result = []
        for s in subs:
            if s.status != "approved" or not s.expires_at:
                continue
            expires = datetime.fromisoformat(s.expires_at)
            delta_days = (expires - now).days
            if 0 <= delta_days <= days:
                result.append(s)
        return result

    async def list_expired_unmarked(self) -> list[VipSubscription]:
        subs = await self.all()
        now = datetime.now(timezone.utc)
        return [
            s
            for s in subs
            if s.status == "approved"
            and s.expires_at
            and datetime.fromisoformat(s.expires_at) <= now
        ]

    async def cumulative_vip_days(self, user_id: int) -> int:
        """Foydalanuvchi UMRI DAVOMIDA olgan (tasdiqlangan) VIP kunlar
        yig'indisi — #VIP Tier tizimi uchun. Muddati tugagan/hali faol
        obunalar ham hisobga olinadi, chunki bu "loyallik" ko'rsatkichi,
        joriy holat emas.
        """

        subs = await self.find_all(lambda s: s.get("user_id") == user_id and s.get("status") == "approved")
        total_days = 0
        for sub in subs:
            if sub.starts_at and sub.expires_at:
                try:
                    start = datetime.fromisoformat(sub.starts_at)
                    end = datetime.fromisoformat(sub.expires_at)
                    total_days += max(0, (end - start).days)
                except ValueError:
                    continue
        return total_days
