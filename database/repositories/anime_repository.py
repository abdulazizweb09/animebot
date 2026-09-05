"""``anime.json`` bilan ishlaydigan repository."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.anime import Anime
from database.repositories.base_repository import BaseRepository


class AnimeRepository(BaseRepository[Anime]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "anime.json", Anime, id_field="code")

    async def get_by_code(self, code: str) -> Anime | None:
        return await self.get(code)

    async def code_exists(self, code: str) -> bool:
        return await self.exists(code)

    async def list_by_genre(self, genre: str) -> list[Anime]:
        animes = await self.all()
        return [a for a in animes if genre.lower() in [g.lower() for g in a.genres]]

    async def list_ongoing(self) -> list[Anime]:
        animes = await self.all()
        return [a for a in animes if a.status == "ongoing"]

    async def increment_views(self, code: str) -> None:
        anime = await self.get(code)
        if anime:
            await self.update(code, {"views": anime.views + 1})

    async def edit(self, code: str, changes: dict) -> Anime | None:
        """Anime ma'lumotlarini yangilaydi va ``updated_at`` ni avtomatik belgilaydi.

        Mavjud ``update()`` metodidan farqli o'laroq, bu metod "Recently
        Updated" ro'yxati uchun kerak bo'lgan ``updated_at`` maydonini har
        doim yangilab turadi. Eski ``update()`` chaqiruvlari (masalan,
        ``soft_delete``, ``increment_views``) o'zgarishsiz qoladi.
        """

        from datetime import datetime, timezone

        changes = {**changes, "updated_at": datetime.now(timezone.utc).isoformat()}
        return await self.update(code, changes)

    async def list_by_studio(self, studio: str) -> list[Anime]:
        animes = await self.all()
        return [a for a in animes if (a.studio or "").lower() == studio.lower()]

    async def list_by_collection(self, collection_id: str) -> list[Anime]:
        animes = await self.all()
        return [a for a in animes if a.collection_id == collection_id]

    async def all_studios(self) -> list[str]:
        animes = await self.all()
        return sorted({a.studio for a in animes if a.studio})

    async def recently_added(self, limit: int = 10) -> list[Anime]:
        animes = await self.all()
        return sorted(animes, key=lambda a: a.created_at, reverse=True)[:limit]

    async def recently_updated(self, limit: int = 10) -> list[Anime]:
        animes = await self.all()
        with_updates = [a for a in animes if a.updated_at]
        return sorted(with_updates, key=lambda a: a.updated_at, reverse=True)[:limit]

    async def most_watched(self, limit: int = 10) -> list[Anime]:
        animes = await self.all()
        return sorted(animes, key=lambda a: a.views, reverse=True)[:limit]

    async def top_rated(self, limit: int = 10, min_votes: int = 1) -> list[Anime]:
        animes = await self.all()
        rated = [a for a in animes if a.rating_count >= min_votes]
        return sorted(rated, key=lambda a: a.average_rating, reverse=True)[:limit]

    async def list_by_type(self, anime_type: str) -> list[Anime]:
        animes = await self.all()
        return [a for a in animes if a.anime_type == anime_type]

    async def advanced_filter(
        self,
        genre: str | None = None,
        year: int | None = None,
        studio: str | None = None,
        status: str | None = None,
        anime_type: str | None = None,
        min_rating: float | None = None,
    ) -> list[Anime]:
        """#29 Advanced Filter — bir nechta mezon bo'yicha birgalikda filtrlash."""

        animes = await self.all()
        result = []
        for a in animes:
            if genre and genre.lower() not in [g.lower() for g in a.genres]:
                continue
            if year and a.year != year:
                continue
            if studio and (a.studio or "").lower() != studio.lower():
                continue
            if status and a.status != status:
                continue
            if anime_type and a.anime_type != anime_type:
                continue
            if min_rating and a.average_rating < min_rating:
                continue
            result.append(a)
        return result

    async def all_years(self) -> list[int]:
        animes = await self.all()
        return sorted({a.year for a in animes if a.year}, reverse=True)

    async def random_one(self, exclude_codes: set[str] | None = None):
        """🎲 Tasodifiy anime — ixtiyoriy ravishda ba'zi kodlarni chetlab
        o'tadi (masalan, foydalanuvchi allaqachon ko'rgan animelarni)."""

        import random

        animes = await self.all()
        if exclude_codes:
            candidates = [a for a in animes if a.code not in exclude_codes]
            if candidates:
                return random.choice(candidates)
        return random.choice(animes) if animes else None

    async def add_rating(self, code: str, score: float) -> None:
        anime = await self.get(code)
        if anime:
            await self.update(
                code,
                {
                    "rating_sum": anime.rating_sum + score,
                    "rating_count": anime.rating_count + 1,
                },
            )

    async def all_titles_for_search(self) -> list[tuple[str, str]]:
        """(code, title) juftliklari — fuzzy search uchun."""

        animes = await self.all()
        return [(a.code, a.title_uz) for a in animes]
