"""Economy (Coins/XP/Level) profili — #48 User Level, #49 XP, #50 Economy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _level_for_xp(xp: int) -> int:
    """Oddiy o'sib boruvchi XP chegarasi: har daraja uchun ``100 * daraja``
    XP kerak (1-daraja: 0-99, 2-daraja: 100-299, 3-daraja: 300-599, ...).
    """

    level = 1
    threshold = 0
    step = 100
    while xp >= threshold + step:
        threshold += step
        step += 100
        level += 1
    return level


@dataclass
class EconomyProfile:
    user_id: int
    coins: int = 0
    xp: int = 0
    level: int = 1
    total_episodes_watched: int = 0
    login_streak: int = 0
    last_daily_claim: str | None = None
    last_login_at: str | None = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, user_id: int, data: dict[str, Any]) -> "EconomyProfile":
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known and k != "user_id"}
        return cls(user_id=user_id, **filtered)

    def recompute_level(self) -> int:
        self.level = _level_for_xp(self.xp)
        return self.level

    def xp_for_next_level(self) -> int:
        """Keyingi darajagacha qancha XP kerakligini qaytaradi."""

        level = 1
        threshold = 0
        step = 100
        while level < self.level:
            threshold += step
            step += 100
            level += 1
        return threshold + step - self.xp
