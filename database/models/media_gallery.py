"""Wallpaper va Trailer galereyasi — #41, #42."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MediaItem:
    id: str  # uuid
    anime_code: str
    kind: str  # "wallpaper" | "trailer"
    file_id: str  # rasm yoki video file_id
    is_deleted: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MediaItem":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
