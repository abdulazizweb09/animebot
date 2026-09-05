"""Anime, Episode va Video modellari."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from config.enums import AgeRestriction, AnimeStatus


@dataclass
class Anime:
    code: str  # noyob kod, masalan "AOT-001"
    title_uz: str
    title_original: str | None = None
    description: str = ""
    poster_file_id: str | None = None
    genres: list[str] = field(default_factory=list)
    year: int | None = None
    status: str = AnimeStatus.ONGOING.value
    age_restriction: str = AgeRestriction.ALL_AGES.value
    is_vip_only: bool = False
    total_episodes_planned: int | None = None
    rating_sum: float = 0.0
    rating_count: int = 0
    views: int = 0
    is_deleted: bool = False
    collection_id: str | None = None  # Anime Collection/Franchise bilan bog'lash uchun
    watch_order: int | None = None  # #31 Timeline, #32 Watch Order, #33 Manga Order
    studio: str | None = None
    anime_type: str = "tv"  # tv/movie/ova/special (#37-39)
    op_songs: list[str] = field(default_factory=list)  # #36 Opening List
    ed_songs: list[str] = field(default_factory=list)  # #36 Ending List
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str | None = None
    created_by: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Anime":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    @property
    def average_rating(self) -> float:
        if self.rating_count == 0:
            return 0.0
        return round(self.rating_sum / self.rating_count, 2)


@dataclass
class Episode:
    id: str  # uuid
    anime_code: str
    number: int
    title: str | None = None
    is_deleted: bool = False
    is_filler: bool = False  # #34 Filler List / #35 Canon List
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Episode":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Video:
    id: str  # uuid
    episode_id: str
    anime_code: str
    file_id: str
    quality: str = "480p"  # 480p / 720p / 1080p
    duration_seconds: int | None = None
    uploaded_by: int | None = None
    uploaded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_deleted: bool = False
    downloads: int = 0  # #51 Download Counter

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Video":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
