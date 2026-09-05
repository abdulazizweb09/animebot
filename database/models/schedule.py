"""Anime chiqish jadvali yozuvi — #20 Calendar, #21 Schedule Notification,
#22 Countdown.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ScheduleEntry:
    id: str  # uuid
    anime_code: str
    episode_number: int
    release_at: str  # ISO datetime — epizod chiqish vaqti
    is_released: bool = False
    notified_1day: bool = False
    notified_1hour: bool = False
    notified_30min: bool = False
    created_by: int | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduleEntry":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def release_datetime(self) -> datetime:
        return datetime.fromisoformat(self.release_at)

    def time_remaining(self) -> "timedelta":
        from datetime import timedelta as _timedelta

        remaining = self.release_datetime() - datetime.now(timezone.utc)
        return remaining if remaining.total_seconds() > 0 else _timedelta(0)
