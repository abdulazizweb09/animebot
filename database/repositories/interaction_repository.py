"""favorites.json va history.json repositorylari."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.interaction import Favorite, HistoryEntry, WatchlistEntry
from database.repositories.base_repository import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "favorites.json", Favorite, id_field="id")

    async def list_for_user(self, user_id: int) -> list[Favorite]:
        items = await self.find_all(lambda f: f.get("user_id") == user_id)
        return [i for i in items if not i.is_deleted]

    async def is_favorite(self, user_id: int, anime_code: str) -> bool:
        item = await self.find_one(
            lambda f: f.get("user_id") == user_id
            and f.get("anime_code") == anime_code
            and not f.get("is_deleted", False)
        )
        return item is not None

    async def remove(self, user_id: int, anime_code: str) -> bool:
        item = await self.find_one(
            lambda f: f.get("user_id") == user_id
            and f.get("anime_code") == anime_code
            and not f.get("is_deleted", False)
        )
        if item is None:
            return False
        return await self.hard_delete(item.id)


class HistoryRepository(BaseRepository[HistoryEntry]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "history.json", HistoryEntry, id_field="id")

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[HistoryEntry]:
        items = await self.find_all(lambda h: h.get("user_id") == user_id)
        items.sort(key=lambda h: h.watched_at, reverse=True)
        return items[:limit]

    async def record(self, user_id: int, anime_code: str, episode_id: str | None) -> None:
        import uuid

        from database.models.interaction import HistoryEntry as _HE

        existing = await self.find_one(
            lambda h: h.get("user_id") == user_id and h.get("anime_code") == anime_code
        )
        entry = _HE(
            id=existing.id if existing else str(uuid.uuid4()),
            user_id=user_id,
            anime_code=anime_code,
            episode_id=episode_id,
        )
        await self.replace(entry)


class WatchlistRepository(BaseRepository[WatchlistEntry]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "watchlist.json", WatchlistEntry, id_field="id")

    async def get_entry(self, user_id: int, anime_code: str) -> WatchlistEntry | None:
        return await self.find_one(
            lambda w: w.get("user_id") == user_id
            and w.get("anime_code") == anime_code
            and not w.get("is_deleted", False)
        )

    async def list_by_status(self, user_id: int, status: str) -> list[WatchlistEntry]:
        items = await self.find_all(
            lambda w: w.get("user_id") == user_id and w.get("status") == status
        )
        items = [i for i in items if not i.is_deleted]
        return sorted(items, key=lambda i: i.updated_at, reverse=True)

    async def upsert(
        self, user_id: int, anime_code: str, status: str, current_episode: int | None = None
    ) -> WatchlistEntry:
        import uuid
        from datetime import datetime, timezone

        existing = await self.get_entry(user_id, anime_code)
        now = datetime.now(timezone.utc).isoformat()

        if existing:
            entry = WatchlistEntry(
                id=existing.id,
                user_id=user_id,
                anime_code=anime_code,
                status=status,
                current_episode=(
                    current_episode if current_episode is not None else existing.current_episode
                ),
                updated_at=now,
            )
        else:
            entry = WatchlistEntry(
                id=str(uuid.uuid4()),
                user_id=user_id,
                anime_code=anime_code,
                status=status,
                current_episode=current_episode or 0,
                updated_at=now,
            )
        await self.replace(entry)
        return entry
