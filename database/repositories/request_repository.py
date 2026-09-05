"""``anime_requests.json`` va ``bug_reports.json`` repositorylari."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.request import AnimeRequest, BugReport
from database.repositories.base_repository import BaseRepository


class AnimeRequestRepository(BaseRepository[AnimeRequest]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "anime_requests.json", AnimeRequest, id_field="id")

    async def list_pending(self) -> list[AnimeRequest]:
        return await self.find_all(lambda r: r.get("status") == "pending")

    async def list_for_user(self, user_id: int) -> list[AnimeRequest]:
        return await self.find_all(lambda r: r.get("user_id") == user_id)

    async def find_similar_pending(self, title: str) -> AnimeRequest | None:
        """Bir xil (harflar registrisiz solishtirilgan) nomdagi kutilayotgan
        so'rov bor-yo'qligini tekshiradi — duplicate so'rov o'rniga
        foydalanuvchi ovoz berishi mumkin bo'lishi uchun."""

        normalized = title.strip().lower()
        pending = await self.list_pending()
        for r in pending:
            if r.title.strip().lower() == normalized:
                return r
        return None

    async def upvote(self, request_id: str, user_id: int) -> AnimeRequest | None:
        """So'rovga ovoz beradi (bitta atomik lock ostida, takroriy ovozning
        oldini olib)."""

        result_holder: dict[str, dict | None] = {"item": None}

        def _updater(data: list[dict]) -> list[dict]:
            for entry in data:
                if entry.get("id") == request_id:
                    upvoted_by: list = entry.get("upvoted_by", [])
                    if user_id not in upvoted_by:
                        upvoted_by.append(user_id)
                    entry["upvoted_by"] = upvoted_by
                    result_holder["item"] = entry
                    return data
            return data

        await self._manager.update(self._filename, _updater, default=[])
        raw = result_holder["item"]
        return AnimeRequest.from_dict(raw) if raw else None


class BugReportRepository(BaseRepository[BugReport]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "bug_reports.json", BugReport, id_field="id")

    async def list_open(self) -> list[BugReport]:
        return await self.find_all(lambda r: r.get("status") == "open")
