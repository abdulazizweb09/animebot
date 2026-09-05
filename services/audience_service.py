"""Maqsadli Broadcast uchun auditoriya segmentlarini aniqlash.

Admin "hammaga" o'rniga "faqat VIP'larga" yoki "faqat muayyan janrni
sevganlarga" xabar yubormoqchi bo'lsa, shu servis mos user_id ro'yxatini
tuzib beradi.
"""

from __future__ import annotations

from database.repositories.anime_repository import AnimeRepository
from database.repositories.interaction_repository import FavoriteRepository
from database.repositories.user_repository import UserRepository
from database.repositories.vip_repository import VipRepository


class AudienceService:
    def __init__(
        self,
        users: UserRepository,
        vips: VipRepository,
        favorites: FavoriteRepository,
        animes: AnimeRepository,
    ) -> None:
        self._users = users
        self._vips = vips
        self._favorites = favorites
        self._animes = animes

    async def vip_user_ids(self) -> list[int]:
        """Hozirda faol VIP obunaga ega barcha foydalanuvchilar."""

        all_users = await self._users.all_active_ids()
        result = []
        for user_id in all_users:
            vip = await self._vips.get_active_for_user(user_id)
            if vip:
                result.append(user_id)
        return result

    async def non_vip_user_ids(self) -> list[int]:
        """VIP bo'lmagan foydalanuvchilar — VIP sotishni targ'ib qilish uchun."""

        all_users = await self._users.all_active_ids()
        vip_ids = set(await self.vip_user_ids())
        return [uid for uid in all_users if uid not in vip_ids]

    async def genre_fans_user_ids(self, genre: str) -> list[int]:
        """Berilgan janrdagi hech bo'lmasa bitta animeni sevimliga
        qo'shgan foydalanuvchilar (yangi anime chiqqanda targ'ib qilish
        uchun qulay)."""

        genre_lower = genre.strip().lower()
        all_animes = await self._animes.all()
        matching_codes = {
            a.code for a in all_animes if genre_lower in [g.lower() for g in a.genres]
        }
        if not matching_codes:
            return []

        favorites = await self._favorites.all()
        return list({f.user_id for f in favorites if f.anime_code in matching_codes})

    async def inactive_user_ids(self, days: int = 14) -> list[int]:
        """So'nggi ``days`` kunda faol bo'lmagan foydalanuvchilar —
        "sizni sog'indik" turdagi xabar uchun."""

        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_users = await self._users.all()
        result = []
        for u in all_users:
            if u.is_banned:
                continue
            if not u.last_active_at:
                continue
            try:
                last_active = datetime.fromisoformat(u.last_active_at)
                if last_active < cutoff:
                    result.append(u.user_id)
            except ValueError:
                continue
        return result
