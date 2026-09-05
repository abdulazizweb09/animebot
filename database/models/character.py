"""Anime personaji — #25 Character Search, #26 Voice Actor Search,
#40 Character Gallery.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Character:
    id: str  # uuid
    anime_code: str
    name: str
    voice_actor: str | None = None  # #26 Voice Actor
    image_file_id: str | None = None  # #40 Character Gallery
    description: str = ""
    is_deleted: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
