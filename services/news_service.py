"""News/Announcements servisi (#43, #44)."""

from __future__ import annotations

import uuid

from database.models.news import NewsPost
from database.repositories.news_repository import NewsRepository


class NewsService:
    def __init__(self, news: NewsRepository) -> None:
        self._news = news

    async def publish(
        self, title: str, content: str, kind: str, created_by: int, image_file_id: str | None = None
    ) -> NewsPost:
        post = NewsPost(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            kind=kind,
            image_file_id=image_file_id,
            created_by=created_by,
        )
        await self._news.add(post)
        return post

    async def recent_news(self, limit: int = 10) -> list[NewsPost]:
        return await self._news.recent(kind="news", limit=limit)

    async def recent_announcements(self, limit: int = 10) -> list[NewsPost]:
        return await self._news.recent(kind="announcement", limit=limit)
