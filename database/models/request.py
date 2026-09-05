"""Anime so'rovi va muammo haqida xabar (bug report) modellari."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AnimeRequest:
    """Foydalanuvchi "botda yo'q anime"ni so'rashi."""

    id: str
    user_id: int
    title: str
    note: str = ""
    status: str = "pending"  # pending | fulfilled | rejected
    admin_comment: str | None = None
    upvoted_by: list[int] = field(default_factory=list)  # duplikat o'rniga ovoz berish
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    decided_at: str | None = None
    decided_by: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnimeRequest":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class BugReport:
    """Foydalanuvchi tomonidan yuborilgan muammo/xato xabari."""

    id: str
    user_id: int
    text: str
    anime_code: str | None = None
    status: str = "open"  # open | resolved
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str | None = None
    resolved_by: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BugReport":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
