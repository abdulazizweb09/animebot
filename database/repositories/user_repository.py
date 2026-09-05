"""``users.json`` bilan ishlaydigan repository."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.user import User
from database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "users.json", User, id_field="user_id")

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.get(user_id)

    async def get_or_none(self, user_id: int) -> User | None:
        return await self.get(user_id)

    async def set_language(self, user_id: int, language: str) -> User | None:
        return await self.update(user_id, {"language": language})

    async def ban(self, user_id: int, reason: str | None = None) -> User | None:
        return await self.update(user_id, {"is_banned": True, "ban_reason": reason})

    async def unban(self, user_id: int) -> User | None:
        return await self.update(user_id, {"is_banned": False, "ban_reason": None})

    async def set_role(self, user_id: int, role: str) -> User | None:
        return await self.update(user_id, {"role": role})

    async def all_active_ids(self) -> list[int]:
        """Broadcast uchun — ban qilinmagan barcha user ID lar."""

        users = await self.all()
        return [u.user_id for u in users if not u.is_banned]

    async def search_by_username_or_id(self, query: str) -> list[User]:
        query = query.strip().lstrip("@").lower()
        users = await self.all()
        result = []
        for u in users:
            if query.isdigit() and str(u.user_id) == query:
                result.append(u)
            elif u.username and query in u.username.lower():
                result.append(u)
        return result

    async def count_total(self) -> int:
        return await self.count()

    async def count_banned(self) -> int:
        users = await self.all()
        return sum(1 for u in users if u.is_banned)
