"""ratings.json, comments.json, notifications.json repositorylari."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.rating import Comment, Notification, UserRating
from database.repositories.base_repository import BaseRepository


class RatingRepository(BaseRepository[UserRating]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "ratings.json", UserRating, id_field="id")

    async def get_user_rating(self, user_id: int, anime_code: str) -> UserRating | None:
        return await self.find_one(
            lambda r: r.get("user_id") == user_id
            and r.get("anime_code") == anime_code
            and not r.get("is_deleted", False)
        )

    async def list_for_anime(self, anime_code: str, limit: int = 20) -> list[UserRating]:
        items = await self.find_all(
            lambda r: r.get("anime_code") == anime_code and not r.get("is_deleted", False)
        )
        return sorted(items, key=lambda r: r.created_at, reverse=True)[:limit]

    async def list_by_user(self, user_id: int) -> list[UserRating]:
        items = await self.find_all(
            lambda r: r.get("user_id") == user_id and not r.get("is_deleted", False)
        )
        return sorted(items, key=lambda r: r.created_at, reverse=True)

    async def anime_stats(self, anime_code: str) -> dict:
        items = await self.list_for_anime(anime_code, limit=10000)
        if not items:
            return {"count": 0, "average": 0.0, "distribution": {}}
        total = sum(r.score for r in items)
        dist = {}
        for r in items:
            dist[r.score] = dist.get(r.score, 0) + 1
        return {
            "count": len(items),
            "average": round(total / len(items), 2),
            "distribution": dist,
        }


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "comments.json", Comment, id_field="id")

    async def list_for_anime(self, anime_code: str, limit: int = 20) -> list[Comment]:
        items = await self.find_all(
            lambda c: c.get("anime_code") == anime_code and not c.get("is_deleted", False)
        )
        return sorted(items, key=lambda c: c.created_at, reverse=True)[:limit]

    async def list_by_user(self, user_id: int) -> list[Comment]:
        return await self.find_all(
            lambda c: c.get("user_id") == user_id and not c.get("is_deleted", False)
        )

    async def recent_all(self, limit: int = 20) -> list[Comment]:
        """Barcha animelar bo'yicha eng so'nggi izohlar — admin moderatsiyasi
        uchun."""

        items = await self.all()
        return sorted(items, key=lambda c: c.created_at, reverse=True)[:limit]

    async def report(self, comment_id: str, user_id: int) -> Comment | None:
        result_holder: dict[str, dict | None] = {"item": None}

        def _updater(data: list[dict]) -> list[dict]:
            for entry in data:
                if entry.get("id") == comment_id:
                    reported_by: list = entry.get("reported_by", [])
                    if user_id not in reported_by:
                        reported_by.append(user_id)
                    entry["reported_by"] = reported_by
                    result_holder["item"] = entry
                    return data
            return data

        await self._manager.update(self._filename, _updater, default=[])
        raw = result_holder["item"]
        return Comment.from_dict(raw) if raw else None

    async def most_reported(self, limit: int = 20) -> list[Comment]:
        items = await self.find_all(
            lambda c: len(c.get("reported_by", [])) > 0 and not c.get("is_deleted", False)
        )
        return sorted(items, key=lambda c: len(c.reported_by), reverse=True)[:limit]

    async def like(self, comment_id: str, user_id: int) -> Comment | None:
        result_holder: dict[str, dict | None] = {"item": None}

        def _updater(data: list[dict]) -> list[dict]:
            for entry in data:
                if entry.get("id") == comment_id:
                    liked_by: list = entry.get("liked_by", [])
                    if user_id in liked_by:
                        liked_by.remove(user_id)
                        entry["likes"] = max(0, entry.get("likes", 0) - 1)
                    else:
                        liked_by.append(user_id)
                        entry["likes"] = entry.get("likes", 0) + 1
                    entry["liked_by"] = liked_by
                    result_holder["item"] = entry
                    return data
            return data

        await self._manager.update(self._filename, _updater, default=[])
        raw = result_holder["item"]
        return Comment.from_dict(raw) if raw else None


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "notifications.json", Notification, id_field="id")

    async def list_for_user(self, user_id: int, limit: int = 20) -> list[Notification]:
        items = await self.find_all(lambda n: n.get("user_id") == user_id)
        return sorted(items, key=lambda n: n.created_at, reverse=True)[:limit]

    async def unread_count(self, user_id: int) -> int:
        items = await self.find_all(
            lambda n: n.get("user_id") == user_id and not n.get("is_read", False)
        )
        return len(items)

    async def mark_all_read(self, user_id: int) -> int:
        marked = 0

        def _updater(data: list[dict]) -> list[dict]:
            nonlocal marked
            for entry in data:
                if entry.get("user_id") == user_id and not entry.get("is_read", False):
                    entry["is_read"] = True
                    marked += 1
            return data

        await self._manager.update(self._filename, _updater, default=[])
        return marked
