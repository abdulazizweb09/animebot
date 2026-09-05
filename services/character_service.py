"""Character/Voice Actor/Gallery servisi (#25, #26, #40, #41, #42)."""

from __future__ import annotations

import uuid

from database.models.character import Character
from database.models.media_gallery import MediaItem
from database.repositories.character_repository import CharacterRepository
from database.repositories.media_gallery_repository import MediaGalleryRepository


class CharacterService:
    def __init__(
        self, characters: CharacterRepository, gallery: MediaGalleryRepository
    ) -> None:
        self._characters = characters
        self._gallery = gallery

    async def add_character(
        self, anime_code: str, name: str, voice_actor: str | None, image_file_id: str | None
    ) -> Character:
        character = Character(
            id=str(uuid.uuid4()),
            anime_code=anime_code,
            name=name,
            voice_actor=voice_actor,
            image_file_id=image_file_id,
        )
        await self._characters.add(character)
        return character

    async def search_by_name(self, query: str) -> list[Character]:
        return await self._characters.search_by_name(query)

    async def search_by_voice_actor(self, query: str) -> list[Character]:
        return await self._characters.search_by_voice_actor(query)

    async def list_for_anime(self, anime_code: str) -> list[Character]:
        return await self._characters.list_for_anime(anime_code)

    async def add_media(self, anime_code: str, kind: str, file_id: str) -> MediaItem:
        item = MediaItem(id=str(uuid.uuid4()), anime_code=anime_code, kind=kind, file_id=file_id)
        await self._gallery.add(item)
        return item

    async def wallpapers(self, anime_code: str) -> list[MediaItem]:
        return await self._gallery.list_for_anime(anime_code, "wallpaper")

    async def trailers(self, anime_code: str) -> list[MediaItem]:
        return await self._gallery.list_for_anime(anime_code, "trailer")
