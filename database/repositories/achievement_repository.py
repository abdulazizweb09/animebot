"""``achievements.json`` repository."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.achievement import Achievement
from database.repositories.base_repository import BaseRepository


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "achievements.json", Achievement, id_field="id")

    async def has_badge(self, user_id: int, badge_code: str) -> bool:
        item = await self.find_one(
            lambda a: a.get("user_id") == user_id and a.get("badge_code") == badge_code
        )
        return item is not None

    async def list_for_user(self, user_id: int) -> list[Achievement]:
        return await self.find_all(lambda a: a.get("user_id") == user_id)

    async def top_by_badge_count(self, limit: int = 10) -> list[tuple[int, int]]:
        """``(user_id, badge_soni)`` — eng ko'p yutuq to'plagan foydalanuvchilar."""

        from collections import Counter

        all_items = await self.all()
        counter: Counter[int] = Counter(a.user_id for a in all_items)
        return counter.most_common(limit)
