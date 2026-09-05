"""Anime kartochkasi va epizodlar bilan bog'liq biznes-mantiq."""

from __future__ import annotations

from database.models.anime import Anime, Episode
from database.repositories.anime_repository import AnimeRepository
from database.repositories.episode_repository import EpisodeRepository, VideoRepository
from services.analytics_service import AnalyticsService


class AnimeService:
    def __init__(
        self,
        animes: AnimeRepository,
        episodes: EpisodeRepository,
        videos: VideoRepository,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._animes = animes
        self._episodes = episodes
        self._videos = videos
        self._analytics = analytics

    async def get_detail(self, code: str) -> Anime | None:
        return await self._animes.get_by_code(code)

    async def get_episodes(self, code: str) -> list[Episode]:
        return await self._episodes.list_for_anime(code)

    async def view_anime(self, code: str, user_id: int | None = None) -> None:
        """Umumiy ko'rishlar sonini oshiradi va (agar ``user_id`` berilgan
        bo'lsa) vaqt-oynali analytics uchun voqea yozadi.

        ``user_id`` ixtiyoriy — eski chaqiruvlar (``view_anime(code)``)
        o'zgarishsiz ishlayveradi.
        """

        await self._animes.increment_views(code)
        if self._analytics is not None and user_id is not None:
            await self._analytics.log_event("anime_view", user_id=user_id, anime_code=code)

    async def get_videos_for_episode(self, episode_id: str):
        return await self._videos.list_for_episode(episode_id)

    async def list_by_category(self, genre: str) -> list[Anime]:
        return await self._animes.list_by_genre(genre)

    async def list_ongoing(self) -> list[Anime]:
        return await self._animes.list_ongoing()

    async def rate(self, code: str, score: float) -> None:
        await self._animes.add_rating(code, score)

    # ------------------------------------------------------------------
    # Discovery: Trending / Most Watched / Top Rated / Recently Added-Updated
    # ------------------------------------------------------------------

    async def recently_added(self, limit: int = 10) -> list[Anime]:
        return await self._animes.recently_added(limit)

    async def recently_updated(self, limit: int = 10) -> list[Anime]:
        return await self._animes.recently_updated(limit)

    async def most_watched(self, limit: int = 10) -> list[Anime]:
        return await self._animes.most_watched(limit)

    async def top_rated(self, limit: int = 10) -> list[Anime]:
        return await self._animes.top_rated(limit)

    async def trending(self, hours: int = 24, limit: int = 10) -> list[Anime]:
        """So'nggi ``hours`` soat ichidagi ko'rishlar asosida trend animelar."""

        if self._analytics is None:
            return await self.most_watched(limit)

        ranked = await self._analytics.trending_anime_codes(hours=hours, limit=limit)
        result = []
        for code, _count in ranked:
            anime = await self._animes.get_by_code(code)
            if anime:
                result.append(anime)
        return result

    async def list_by_studio(self, studio: str) -> list[Anime]:
        return await self._animes.list_by_studio(studio)

    async def all_studios(self) -> list[str]:
        return await self._animes.all_studios()

    # ------------------------------------------------------------------
    # #29 Advanced Filter, #37-39 Movie/OVA/Special lists, #30 Compare
    # ------------------------------------------------------------------

    async def list_by_type(self, anime_type: str) -> list[Anime]:
        return await self._animes.list_by_type(anime_type)

    async def advanced_filter(self, **criteria) -> list[Anime]:
        return await self._animes.advanced_filter(**criteria)

    async def all_years(self) -> list[int]:
        return await self._animes.all_years()

    async def filler_episodes(self, anime_code: str) -> list[Episode]:
        return await self._episodes.filler_episodes(anime_code)

    async def canon_episodes(self, anime_code: str) -> list[Episode]:
        return await self._episodes.canon_episodes(anime_code)

    async def random_one(self, exclude_codes: set[str] | None = None):
        """🎲 Tasodifiy anime."""

        return await self._animes.random_one(exclude_codes)

    async def compare(self, code_a: str, code_b: str) -> tuple[Anime | None, Anime | None]:
        anime_a = await self._animes.get_by_code(code_a)
        anime_b = await self._animes.get_by_code(code_b)
        return anime_a, anime_b
