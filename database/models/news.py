"""Anime News / Announcements — #43, #44."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class NewsPost:
    id: str  # uuid
    title: str
    content: str
    kind: str = "news"  # "news" | "announcement"
    image_file_id: str | None = None
    is_deleted: bool = False
    created_by: int | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewsPost":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
