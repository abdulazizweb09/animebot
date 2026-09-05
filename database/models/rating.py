"""Foydalanuvchi bahosi va izoh modellari."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class UserRating:
    """Bitta foydalanuvchining bitta anime uchun bahosi + ixtiyoriy sharh."""

    id: str          # uuid
    user_id: int
    anime_code: str
    score: int       # 1–10
    review: str = "" # ixtiyoriy matlli sharh
    is_deleted: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserRating":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Comment:
    """Anime uchun foydalanuvchi izohi."""

    id: str
    user_id: int
    anime_code: str
    text: str
    is_deleted: bool = False
    likes: int = 0
    liked_by: list[int] = field(default_factory=list)
    reported_by: list[int] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Comment":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Notification:
    """Foydalanuvchiga yuborilgan in-bot bildirishnoma."""

    id: str
    user_id: int
    kind: str        # "new_episode" | "vip_expiring" | "achievement" | "system" | "custom"
    title: str
    text: str
    anime_code: str | None = None
    is_read: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
