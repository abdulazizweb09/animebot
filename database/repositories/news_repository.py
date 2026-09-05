"""``news.json`` repository — #43, #44."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.news import NewsPost
from database.repositories.base_repository import BaseRepository


class NewsRepository(BaseRepository[NewsPost]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "news.json", NewsPost, id_field="id")

    async def recent(self, kind: str | None = None, limit: int = 10) -> list[NewsPost]:
        items = await self.all()
        if kind:
            items = [i for i in items if i.kind == kind]
        return sorted(items, key=lambda i: i.created_at, reverse=True)[:limit]
