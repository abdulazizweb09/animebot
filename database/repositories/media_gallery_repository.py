"""``media_gallery.json`` repository — #41 Wallpaper, #42 Trailer."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.media_gallery import MediaItem
from database.repositories.base_repository import BaseRepository


class MediaGalleryRepository(BaseRepository[MediaItem]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "media_gallery.json", MediaItem, id_field="id")

    async def list_for_anime(self, anime_code: str, kind: str) -> list[MediaItem]:
        return await self.find_all(
            lambda m: m.get("anime_code") == anime_code and m.get("kind") == kind
        )
