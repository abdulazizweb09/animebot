"""Ko'rish tarixi bilan ishlash logikasi."""

from __future__ import annotations

from database.models.interaction import HistoryEntry
from database.repositories.interaction_repository import HistoryRepository


class HistoryService:
    def __init__(self, history: HistoryRepository) -> None:
        self._history = history

    async def record(self, user_id: int, anime_code: str, episode_id: str | None = None) -> None:
        await self._history.record(user_id, anime_code, episode_id)

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[HistoryEntry]:
        return await self._history.list_for_user(user_id, limit)
