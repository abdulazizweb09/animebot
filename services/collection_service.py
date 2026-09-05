"""Anime Collection / Franchise bilan ishlash logikasi."""

from __future__ import annotations

import uuid

from database.models.collection import AnimeCollection
from database.repositories.anime_repository import AnimeRepository
from database.repositories.collection_repository import CollectionRepository


class CollectionService:
    def __init__(self, collections: CollectionRepository, animes: AnimeRepository) -> None:
        self._collections = collections
        self._animes = animes

    async def create(
        self, title: str, description: str, created_by: int, poster_file_id: str | None = None
    ) -> AnimeCollection:
        collection = AnimeCollection(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            poster_file_id=poster_file_id,
            created_by=created_by,
        )
        await self._collections.add(collection)
        return collection

    async def attach_anime(self, collection_id: str, anime_code: str) -> bool:
        if not await self._collections.exists(collection_id):
            return False
        if not await self._animes.exists(anime_code):
            return False
        await self._animes.edit(anime_code, {"collection_id": collection_id})
        return True

    async def detach_anime(self, anime_code: str) -> None:
        await self._animes.edit(anime_code, {"collection_id": None})

    async def list_all(self) -> list[AnimeCollection]:
        return await self._collections.all()

    async def get(self, collection_id: str) -> AnimeCollection | None:
        return await self._collections.get(collection_id)

    async def get_animes(self, collection_id: str) -> list:
        return await self._animes.list_by_collection(collection_id)

    async def get_animes_by_timeline(self, collection_id: str) -> list:
        """#31 Anime Timeline — chiqarilgan yili bo'yicha xronologik tartib
        (voqealar tarixi emas, nashr yili bo'yicha)."""

        animes = await self._animes.list_by_collection(collection_id)
        return sorted(animes, key=lambda a: (a.year or 0, a.title_uz))

    async def get_animes_watch_order(self, collection_id: str) -> list:
        """#32 Watch Order Generator va #33 Manga Order — admin
        belgilagan ``watch_order`` bo'yicha tartib (agar belgilanmagan
        bo'lsa, yil bo'yicha xronologik tartibga tushib qoladi).
        """

        animes = await self._animes.list_by_collection(collection_id)
        return sorted(
            animes,
            key=lambda a: (
                a.watch_order if a.watch_order is not None else 999_999,
                a.year or 0,
                a.title_uz,
            ),
        )

    async def set_watch_order(self, anime_code: str, order: int) -> bool:
        if not await self._animes.exists(anime_code):
            return False
        await self._animes.edit(anime_code, {"watch_order": order})
        return True

    async def delete(self, collection_id: str) -> bool:
        animes = await self.get_animes(collection_id)
        for anime in animes:
            await self._animes.edit(anime.code, {"collection_id": None})
        return await self._collections.soft_delete(collection_id)
