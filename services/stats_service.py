"""📊 Statistika hisoblash logikasi."""

from __future__ import annotations

from database.repositories.anime_repository import AnimeRepository
from database.repositories.user_repository import UserRepository
from database.repositories.vip_repository import VipRepository


class StatsService:
    def __init__(
        self, users: UserRepository, animes: AnimeRepository, vips: VipRepository
    ) -> None:
        self._users = users
        self._animes = animes
        self._vips = vips

    async def summary(self) -> dict:
        total_users = await self._users.count_total()
        banned_users = await self._users.count_banned()
        total_animes = await self._animes.count()
        vip_subs = await self._vips.all()
        active_vip = sum(1 for v in vip_subs if v.is_active())

        animes = await self._animes.all()
        total_views = sum(a.views for a in animes)
        top_animes = sorted(animes, key=lambda a: a.views, reverse=True)[:5]

        return {
            "total_users": total_users,
            "banned_users": banned_users,
            "total_animes": total_animes,
            "active_vip": active_vip,
            "total_views": total_views,
            "top_animes": [(a.title_uz, a.views) for a in top_animes],
        }
