"""Economy (Coins/XP/Level) va Daily Reward/Login logikasi
(#13, #14, #48, #49, #50).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database.models.economy import EconomyProfile
from database.repositories.economy_repository import EconomyRepository
from utils.logger import get_logger

logger = get_logger(__name__)

# Kunlik bonus miqdorlari
DAILY_BASE_COINS = 50
DAILY_BASE_XP = 20
DAILY_STREAK_BONUS_COINS = 10  # har bir ketma-ket kun uchun qo'shimcha
DAILY_STREAK_MAX_BONUS_DAYS = 7

# Har bir ko'rilgan epizod uchun mukofot
XP_PER_EPISODE = 10
COINS_PER_EPISODE = 5


class DailyAlreadyClaimedError(Exception):
    """Foydalanuvchi bugungi kunlik bonusni allaqachon olgan."""

    def __init__(self, next_claim_at: datetime) -> None:
        self.next_claim_at = next_claim_at
        super().__init__("Kunlik bonus allaqachon olingan.")


class EconomyService:
    def __init__(self, economy: EconomyRepository, vip_service=None) -> None:
        self._economy = economy
        self._vip_service = vip_service

    async def get_profile(self, user_id: int) -> EconomyProfile:
        return await self._economy.get(user_id)

    async def add_xp(self, user_id: int, amount: int) -> EconomyProfile:
        profile = await self._economy.get(user_id)
        profile.xp += amount
        old_level = profile.level
        new_level = profile.recompute_level()
        await self._economy.save(profile)
        if new_level > old_level:
            logger.info("Foydalanuvchi %s darajasi oshdi: %s -> %s", user_id, old_level, new_level)
        return profile

    async def add_coins(self, user_id: int, amount: int) -> EconomyProfile:
        profile = await self._economy.get(user_id)
        profile.coins += amount
        await self._economy.save(profile)
        return profile

    async def reward_episode_watched(self, user_id: int) -> EconomyProfile:
        """Har bir ko'rilgan epizod uchun XP+coin beradi va umumiy
        ko'rilgan-epizodlar sonini oshiradi (#48-50, achievement uchun asos).
        """

        profile = await self._economy.get(user_id)
        profile.xp += XP_PER_EPISODE
        profile.coins += COINS_PER_EPISODE
        profile.total_episodes_watched += 1
        profile.recompute_level()
        await self._economy.save(profile)
        return profile

    async def claim_daily(self, user_id: int) -> tuple[EconomyProfile, int, int]:
        """#13 Daily Reward, #14 Daily Login.

        Qaytaradi: ``(profil, olingan_coin, olingan_xp)``.
        24 soat o'tmagan bo'lsa ``DailyAlreadyClaimedError`` ko'taradi.
        """

        profile = await self._economy.get(user_id)
        now = datetime.now(timezone.utc)

        if profile.last_daily_claim:
            last = datetime.fromisoformat(profile.last_daily_claim)
            elapsed = now - last
            if elapsed < timedelta(hours=24):
                next_claim = last + timedelta(hours=24)
                raise DailyAlreadyClaimedError(next_claim)
            if elapsed < timedelta(hours=48):
                profile.login_streak += 1
            else:
                profile.login_streak = 1
        else:
            profile.login_streak = 1

        streak_bonus = min(profile.login_streak, DAILY_STREAK_MAX_BONUS_DAYS) * DAILY_STREAK_BONUS_COINS
        coins_earned = DAILY_BASE_COINS + streak_bonus
        xp_earned = DAILY_BASE_XP

        if self._vip_service is not None:
            tier = await self._vip_service.get_tier(user_id)
            coins_earned = round(coins_earned * tier.daily_bonus_multiplier)

        profile.coins += coins_earned
        profile.xp += xp_earned
        profile.last_daily_claim = now.isoformat()
        profile.last_login_at = now.isoformat()
        profile.recompute_level()

        await self._economy.save(profile)
        return profile, coins_earned, xp_earned

    async def leaderboard(self, by: str = "xp", limit: int = 10) -> list[EconomyProfile]:
        """#47 Leaderboard — ``by`` "xp" yoki "coins" bo'lishi mumkin."""

        if by == "coins":
            return await self._economy.top_by_coins(limit)
        return await self._economy.top_by_xp(limit)

    async def spend_coins(self, user_id: int, amount: int) -> bool:
        """Tanga Do'koni uchun — mablag' yetarli bo'lsa yechadi va
        ``True`` qaytaradi, aks holda ``False``."""

        return await self._economy.try_spend(user_id, amount)
