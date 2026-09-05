"""Sevimlilar va ko'rish tarixi modellari."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Favorite:
    id: str  # uuid
    user_id: int
    anime_code: str
    is_deleted: bool = False
    added_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Favorite":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class HistoryEntry:
    id: str  # uuid
    user_id: int
    anime_code: str
    episode_id: str | None = None
    is_deleted: bool = False
    watched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class WatchlistEntry:
    """Bookmark folder yozuvi: foydalanuvchining anime bo'yicha ko'rish holati
    va progressi (#9 Continue Watching, #10 Progress, #11 Completion%,
    #53 Bookmark Folder).
    """

    id: str  # uuid
    user_id: int
    anime_code: str
    status: str = "plan_to_watch"
    current_episode: int = 0
    is_deleted: bool = False
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WatchlistEntry":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
