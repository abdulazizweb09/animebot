"""Achievement (badge) berish logikasi (#12)."""

from __future__ import annotations

import uuid

from config.badges import (
    AI_USER_BADGE,
    EPISODE_MILESTONES,
    VIP_BADGE,
    VIP_GOLD_BADGE,
    VIP_SILVER_BADGE,
    BadgeDefinition,
)
from config.enums import VipTier
from database.models.achievement import Achievement
from database.repositories.achievement_repository import AchievementRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class AchievementService:
    def __init__(self, achievements: AchievementRepository) -> None:
        self._achievements = achievements

    async def _award(self, user_id: int, badge: BadgeDefinition) -> bool:
        """Badge bergan bo'lsa ``True``, allaqachon bor bo'lsa ``False``
        qaytaradi (idempotent — bir xil badge ikki marta berilmaydi).
        """

        if await self._achievements.has_badge(user_id, badge.code):
            return False

        await self._achievements.add(
            Achievement(id=str(uuid.uuid4()), user_id=user_id, badge_code=badge.code)
        )
        logger.info("Badge berildi: user=%s badge=%s", user_id, badge.code)
        return True

    async def check_episode_milestones(
        self, user_id: int, total_watched: int
    ) -> list[BadgeDefinition]:
        """Epizod-soni chegaralarini tekshiradi (100/500/1000) va yangi
        berilgan badge'larni qaytaradi (handler bularni userga xabar
        qilishi mumkin).
        """

        newly_awarded = []
        for threshold, badge in sorted(EPISODE_MILESTONES.items()):
            if total_watched >= threshold:
                if await self._award(user_id, badge):
                    newly_awarded.append(badge)
        return newly_awarded

    async def award_vip_badge(self, user_id: int) -> bool:
        return await self._award(user_id, VIP_BADGE)

    async def award_vip_tier_badge(self, user_id: int, tier: VipTier) -> BadgeDefinition | None:
        """VIP loyallik darajasiga mos badge beradi (Silver/Gold)."""

        badge_map = {VipTier.SILVER: VIP_SILVER_BADGE, VipTier.GOLD: VIP_GOLD_BADGE}
        badge = badge_map.get(tier)
        if badge is None:
            return None
        awarded = await self._award(user_id, badge)
        return badge if awarded else None

    async def award_ai_user_badge(self, user_id: int) -> bool:
        return await self._award(user_id, AI_USER_BADGE)

    async def list_for_user(self, user_id: int) -> list[Achievement]:
        return await self._achievements.list_for_user(user_id)

    async def leaderboard(self, limit: int = 10) -> list[tuple[int, int]]:
        """#Achievement Leaderboard — eng ko'p yutuq to'plaganlar."""

        return await self._achievements.top_by_badge_count(limit)
