"""Bookmark Folder / Continue Watching / Progress / Completion% logikasi
(#9, #10, #11, #53).
"""

from __future__ import annotations

from config.enums import WatchStatus
from database.models.interaction import WatchlistEntry
from database.repositories.anime_repository import AnimeRepository
from database.repositories.episode_repository import EpisodeRepository
from database.repositories.interaction_repository import WatchlistRepository


class WatchlistService:
    def __init__(
        self,
        watchlist: WatchlistRepository,
        animes: AnimeRepository,
        episodes: EpisodeRepository,
    ) -> None:
        self._watchlist = watchlist
        self._animes = animes
        self._episodes = episodes

    async def set_status(
        self, user_id: int, anime_code: str, status: WatchStatus
    ) -> WatchlistEntry:
        return await self._watchlist.upsert(user_id, anime_code, status.value)

    async def get_status(self, user_id: int, anime_code: str) -> WatchlistEntry | None:
        return await self._watchlist.get_entry(user_id, anime_code)

    async def list_folder(self, user_id: int, status: WatchStatus) -> list[WatchlistEntry]:
        return await self._watchlist.list_by_status(user_id, status.value)

    async def record_progress(self, user_id: int, anime_code: str, episode_number: int) -> None:
        """Foydalanuvchi video ko'rganda avtomatik chaqiriladi: statusni
        "watching"ga o'tkazadi (agar tugallanmagan bo'lsa) va progressni
        yangilaydi. Agar barcha epizodlar ko'rilgan bo'lsa — "completed".
        """

        existing = await self._watchlist.get_entry(user_id, anime_code)
        if existing and existing.status == WatchStatus.COMPLETED.value:
            # Foydalanuvchi tugatgan animeni qayta ko'rsa ham, holatni
            # avtomatik o'zgartirmaymiz — bu foydalanuvchining o'zi
            # tanlagan holat, faqat progressni yangilaymiz.
            await self._watchlist.upsert(
                user_id, anime_code, existing.status, current_episode=episode_number
            )
            return

        episodes = await self._episodes.list_for_anime(anime_code)
        total = len(episodes)
        new_status = WatchStatus.WATCHING
        if total and episode_number >= total:
            new_status = WatchStatus.COMPLETED

        await self._watchlist.upsert(
            user_id, anime_code, new_status.value, current_episode=episode_number
        )

    async def progress_percent(self, user_id: int, anime_code: str) -> float | None:
        entry = await self._watchlist.get_entry(user_id, anime_code)
        if entry is None:
            return None

        episodes = await self._episodes.list_for_anime(anime_code)
        total = len(episodes)
        if not total:
            return None
        return round(min(entry.current_episode, total) / total * 100, 1)

    async def progress_text(self, user_id: int, anime_code: str) -> str | None:
        """``"350 / 500"`` formatidagi matn (#10 Anime Progress)."""

        entry = await self._watchlist.get_entry(user_id, anime_code)
        if entry is None:
            return None
        episodes = await self._episodes.list_for_anime(anime_code)
        total = len(episodes)
        return f"{entry.current_episode} / {total}"

    async def continue_watching(self, user_id: int, limit: int = 10):
        """#9 Continue Watching Slider — "watching" holatidagi animelar,
        oxirgi yangilangani birinchi.
        """

        entries = await self.list_folder(user_id, WatchStatus.WATCHING)
        animes = []
        for entry in entries[:limit]:
            anime = await self._animes.get_by_code(entry.anime_code)
            if anime:
                animes.append(anime)
        return animes
