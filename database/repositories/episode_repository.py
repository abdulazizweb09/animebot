"""``episodes.json`` va ``videos.json`` repositorylari."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.anime import Episode, Video
from database.repositories.base_repository import BaseRepository


class EpisodeRepository(BaseRepository[Episode]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "episodes.json", Episode, id_field="id")

    async def list_for_anime(self, anime_code: str) -> list[Episode]:
        episodes = await self.all()
        result = [e for e in episodes if e.anime_code == anime_code]
        return sorted(result, key=lambda e: e.number)

    async def get_by_number(self, anime_code: str, number: int) -> Episode | None:
        return await self.find_one(
            lambda e: e.get("anime_code") == anime_code and e.get("number") == number
        )

    async def next_number(self, anime_code: str) -> int:
        episodes = await self.list_for_anime(anime_code)
        return (max((e.number for e in episodes), default=0)) + 1

    async def filler_episodes(self, anime_code: str) -> list["Episode"]:
        """#34 Filler List."""
        episodes = await self.list_for_anime(anime_code)
        return [e for e in episodes if e.is_filler]

    async def canon_episodes(self, anime_code: str) -> list["Episode"]:
        """#35 Canon List."""
        episodes = await self.list_for_anime(anime_code)
        return [e for e in episodes if not e.is_filler]

    async def add_with_auto_number(self, anime_code: str, episode_factory) -> "Episode":
        """Qism raqamini va yozishni BITTA lock ostida, atomik bajaradi.

        ``next_number()`` + ``add()`` ni ketma-ket (ikkita alohida lock bilan)
        chaqirish xavfli — agar bir nechta so'rov bir vaqtda kelsa (masalan,
        bulk video yuklashda 100 ta video tez-tez yuborilganda), ikkalasi ham
        bir xil "keyingi raqam"ni o'qib, bir xil raqamli ikkita qism yaratib
        qo'yishi mumkin (race condition). Bu metod butun jarayonni
        ``JsonManager.update()`` ichida, bitta faylga xos lock ostida
        bajarib, bunday to'qnashuvning oldini oladi.

        ``episode_factory`` — ``next_number: int`` argumentini qabul qilib,
        yangi ``Episode`` obyektini qaytaruvchi funksiya (masalan,
        ``lambda n: Episode(id=str(uuid.uuid4()), anime_code=code, number=n)``).
        """

        result_holder: dict[str, Episode] = {}

        def _updater(data: list[dict]) -> list[dict]:
            existing_numbers = [
                d.get("number", 0) for d in data if d.get("anime_code") == anime_code
            ]
            next_number = (max(existing_numbers, default=0)) + 1

            episode = episode_factory(next_number)
            result_holder["episode"] = episode
            data.append(episode.to_dict())
            return data

        await self._manager.update(self._filename, _updater, default=[])
        return result_holder["episode"]


class VideoRepository(BaseRepository[Video]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "videos.json", Video, id_field="id")

    async def list_for_episode(self, episode_id: str) -> list[Video]:
        videos = await self.all()
        return [v for v in videos if v.episode_id == episode_id]

    async def get_by_quality(self, episode_id: str, quality: str) -> Video | None:
        return await self.find_one(
            lambda v: v.get("episode_id") == episode_id and v.get("quality") == quality
        )

    async def file_id_exists(self, file_id: str) -> bool:
        return await self.find_one(lambda v: v.get("file_id") == file_id) is not None

    async def increment_downloads(self, video_id: str) -> None:
        video = await self.get(video_id)
        if video:
            await self.update(video_id, {"downloads": video.downloads + 1})
