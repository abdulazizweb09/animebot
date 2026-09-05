"""Shaxsiy statistika ("Mening statistikam") — foydalanuvchining o'z
faoliyati bo'yicha umumlashtirilgan hisobot.

``HealthService`` bilan bir xil sababga ko'ra (butun ``Container``ga
ehtiyoj bor, lekin ``container.py`` ham shu servisni import qiladi),
circular import'ning oldini olish uchun ``TYPE_CHECKING`` naqshi
ishlatiladi va instansiya ``container.py`` da Container yaratilgandan
KEYIN alohida ulanadi.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from config.enums import WatchStatus

if TYPE_CHECKING:
    from container import Container


class PersonalStatsService:
    def __init__(self, container: "Container") -> None:
        self._container = container

    async def build_summary(self, user_id: int) -> dict:
        container = self._container

        history = await container.history.list_for_user(user_id, limit=10000)
        watched_codes = {h.anime_code for h in history}

        favorites = await container.favorites.list_for_user(user_id)
        economy = await container.economy_service.get_profile(user_id)
        achievements = await container.achievement_service.list_for_user(user_id)
        vip = await container.vips.get_active_for_user(user_id)

        # Eng ko'p ko'rilgan janr
        genre_counter: Counter = Counter()
        for code in watched_codes:
            anime = await container.animes.get_by_code(code)
            if anime:
                for genre in anime.genres:
                    genre_counter[genre] += 1
        top_genre = genre_counter.most_common(1)[0][0] if genre_counter else None

        # Taxminiy tomosha vaqti: har epizod ~24 daqiqa deb hisoblanadi
        estimated_minutes = economy.total_episodes_watched * 24

        watching = await container.watchlist_service.list_folder(user_id, WatchStatus.WATCHING)
        completed = await container.watchlist_service.list_folder(user_id, WatchStatus.COMPLETED)

        return {
            "unique_anime_watched": len(watched_codes),
            "total_episodes_watched": economy.total_episodes_watched,
            "estimated_hours": round(estimated_minutes / 60, 1),
            "favorites_count": len(favorites),
            "top_genre": top_genre,
            "xp": economy.xp,
            "level": economy.level,
            "coins": economy.coins,
            "achievements_count": len(achievements),
            "is_vip": vip is not None,
            "watching_count": len(watching),
            "completed_count": len(completed),
            "login_streak": economy.login_streak,
        }
