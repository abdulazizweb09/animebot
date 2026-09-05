"""Referral tizimi logikasi (#15)."""

from __future__ import annotations

import uuid

from database.models.referral import ReferralRecord
from database.repositories.economy_repository import EconomyRepository
from database.repositories.referral_repository import ReferralRepository
from database.repositories.user_repository import UserRepository
from utils.logger import get_logger

logger = get_logger(__name__)

REFERRAL_REWARD_COINS = 100
REFERRAL_REWARD_XP = 50


class ReferralService:
    def __init__(
        self,
        referrals: ReferralRepository,
        economy: EconomyRepository,
        users: UserRepository,
    ) -> None:
        self._referrals = referrals
        self._economy = economy
        self._users = users

    @staticmethod
    def build_referral_link(bot_username: str, referrer_id: int) -> str:
        return f"https://t.me/{bot_username}?start=ref_{referrer_id}"

    @staticmethod
    def parse_referrer_id(start_param: str | None) -> int | None:
        if not start_param or not start_param.startswith("ref_"):
            return None
        raw = start_param[len("ref_"):]
        return int(raw) if raw.isdigit() else None

    async def register_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Yangi referalni ro'yxatga oladi va mukofot beradi.

        ``False`` qaytaradi: o'z-o'zini referal qilish, allaqachon referal
        qilingan, yoki referrer mavjud bo'lmasa.
        """

        if referrer_id == referred_id:
            return False
        if await self._referrals.already_referred(referred_id):
            return False
        referrer = await self._users.get_by_id(referrer_id)
        if referrer is None:
            return False

        record = ReferralRecord(
            id=str(uuid.uuid4()), referrer_id=referrer_id, referred_id=referred_id
        )
        await self._referrals.add(record)

        profile = await self._economy.get(referrer_id)
        profile.coins += REFERRAL_REWARD_COINS
        profile.xp += REFERRAL_REWARD_XP
        profile.recompute_level()
        await self._economy.save(profile)

        await self._referrals.update(record.id, {"rewarded": True})
        logger.info("Referral ro'yxatga olindi: referrer=%s referred=%s", referrer_id, referred_id)
        return True

    async def count_referrals(self, referrer_id: int) -> int:
        return await self._referrals.count_by_referrer(referrer_id)

    async def leaderboard(self, limit: int = 10) -> list[tuple[int, int]]:
        """#Referral Leaderboard — eng ko'p do'st taklif qilganlar."""

        return await self._referrals.top_referrers(limit)
