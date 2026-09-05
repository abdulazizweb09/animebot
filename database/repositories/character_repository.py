"""``characters.json`` repository — #25, #26, #40."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.character import Character
from database.repositories.base_repository import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "characters.json", Character, id_field="id")

    async def list_for_anime(self, anime_code: str) -> list[Character]:
        return await self.find_all(lambda c: c.get("anime_code") == anime_code)

    async def search_by_name(self, query: str) -> list[Character]:
        query = query.lower().strip()
        chars = await self.all()
        return [c for c in chars if query in c.name.lower()]

    async def search_by_voice_actor(self, query: str) -> list[Character]:
        query = query.lower().strip()
        chars = await self.all()
        return [c for c in chars if c.voice_actor and query in c.voice_actor.lower()]

    async def all_voice_actors(self) -> list[str]:
        chars = await self.all()
        return sorted({c.voice_actor for c in chars if c.voice_actor})
