"""``referrals.json`` repository."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.referral import ReferralRecord
from database.repositories.base_repository import BaseRepository


class ReferralRepository(BaseRepository[ReferralRecord]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "referrals.json", ReferralRecord, id_field="id")

    async def already_referred(self, referred_id: int) -> bool:
        item = await self.find_one(lambda r: r.get("referred_id") == referred_id)
        return item is not None

    async def list_by_referrer(self, referrer_id: int) -> list[ReferralRecord]:
        return await self.find_all(lambda r: r.get("referrer_id") == referrer_id)

    async def count_by_referrer(self, referrer_id: int) -> int:
        items = await self.list_by_referrer(referrer_id)
        return len(items)

    async def top_referrers(self, limit: int = 10) -> list[tuple[int, int]]:
        """``(referrer_id, referal_soni)`` — eng ko'p taklif qilganlar,
        kamayish tartibida."""

        from collections import Counter

        all_records = await self.all()
        counter: Counter[int] = Counter(r.referrer_id for r in all_records)
        return counter.most_common(limit)
