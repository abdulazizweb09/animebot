"""Anime Collection / Franchise modeli.

Bitta collection bir nechta anime'ni ("Naruto", "Naruto Shippuden",
"Boruto" kabi) bitta nom ostida guruhlaydi. Har bir ``Anime`` yozuvi
``collection_id`` orqali shu collectionga bog'lanadi (franchise bog'lanishi
ham aynan shu mexanizm orqali amalga oshadi — alohida duplicate tizim
yaratilmadi).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AnimeCollection:
    id: str  # uuid
    title: str
    description: str = ""
    poster_file_id: str | None = None
    is_deleted: bool = False
    created_by: int | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnimeCollection":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
