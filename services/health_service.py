"""#58 Performance Analyzer, #59 Health Dashboard."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from container import Container

_PROCESS_START_TIME = time.monotonic()


class HealthService:
    def __init__(self, container: "Container") -> None:
        self._container = container

    async def snapshot(self) -> dict:
        """Botning joriy holati haqida umumlashtirilgan hisobot."""

        manager = self._container.manager
        cache_stats = manager.cache_stats()

        uptime_seconds = int(time.monotonic() - _PROCESS_START_TIME)

        users_count = await self._container.users.count_total()
        animes_count = await self._container.animes.count()
        episodes_count = await self._container.episodes.count()
        videos_count = await self._container.videos.count()

        events_24h = await self._container.analytics_service.count_since("anime_view", 24)
        searches_24h = await self._container.analytics_service.count_since("search", 24)
        ai_requests_24h = await self._container.analytics_service.count_since("ai_request", 24)
        vip_requests_24h = await self._container.analytics_service.count_since("vip_request", 24)
        promo_redeems_24h = await self._container.analytics_service.count_since("promo_redeem", 24)
        quiz_answers_24h = await self._container.analytics_service.count_since("quiz_answer", 24)
        referrals_24h = await self._container.analytics_service.count_since(
            "referral_registered", 24
        )
        file_sizes = await self._container.maintenance_service.file_sizes()
        total_size_kb = round(sum(file_sizes.values()) / 1024, 1)

        return {
            "uptime_seconds": uptime_seconds,
            "cache_entries": cache_stats["entries"],
            "cache_max_entries": cache_stats["max_entries"],
            "cache_ttl_seconds": cache_stats["ttl_seconds"],
            "users_count": users_count,
            "animes_count": animes_count,
            "episodes_count": episodes_count,
            "videos_count": videos_count,
            "anime_views_last_24h": events_24h,
            "searches_last_24h": searches_24h,
            "ai_requests_last_24h": ai_requests_24h,
            "vip_requests_last_24h": vip_requests_24h,
            "promo_redeems_last_24h": promo_redeems_24h,
            "quiz_answers_last_24h": quiz_answers_24h,
            "referrals_last_24h": referrals_24h,
            "json_total_size_kb": total_size_kb,
            "json_file_count": len(file_sizes),
        }

    @staticmethod
    def format_uptime(seconds: int) -> str:
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}k")
        if hours:
            parts.append(f"{hours}s")
        parts.append(f"{minutes}d")
        return " ".join(parts)
