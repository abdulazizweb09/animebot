"""``collections.json`` repository."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.collection import AnimeCollection
from database.repositories.base_repository import BaseRepository


class CollectionRepository(BaseRepository[AnimeCollection]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "collections.json", AnimeCollection, id_field="id")
