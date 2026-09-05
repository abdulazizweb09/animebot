"""Poll System (#45) va Quiz System (#46) modellari."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Poll:
    id: str  # uuid
    question: str
    options: list[str] = field(default_factory=list)
    votes: dict[str, int] = field(default_factory=dict)  # {"<user_id>": option_index}
    is_active: bool = True
    created_by: int | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Poll":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def results(self) -> list[int]:
        counts = [0] * len(self.options)
        for option_index in self.votes.values():
            if 0 <= option_index < len(counts):
                counts[option_index] += 1
        return counts


@dataclass
class QuizQuestion:
    id: str  # uuid
    question: str
    options: list[str] = field(default_factory=list)
    correct_index: int = 0
    anime_code: str | None = None
    is_deleted: bool = False
    created_by: int | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuizQuestion":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
