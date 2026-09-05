"""``search_history.json`` — foydalanuvchi qidiruv tarixi."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.repositories.base_repository import BaseRepository


from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SearchHistoryEntry:
    id: str
    user_id: int
    query: str
    results_count: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchHistoryEntry":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


class SearchHistoryRepository(BaseRepository[SearchHistoryEntry]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "search_history.json", SearchHistoryEntry, id_field="id")

    async def recent_for_user(self, user_id: int, limit: int = 10) -> list[SearchHistoryEntry]:
        items = await self.find_all(lambda e: e.get("user_id") == user_id)
        items.sort(key=lambda e: e.created_at, reverse=True)
        # Takroriy so'rovlarni chetlab, faqat noyoblarini qaytaramiz
        seen: set[str] = set()
        unique = []
        for item in items:
            key = item.query.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
            if len(unique) >= limit:
                break
        return unique
