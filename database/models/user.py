"""User model — ``users.json`` dagi bitta yozuvning tipizatsiyalangan ko'rinishi."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from config.enums import UserLanguage, UserRole


@dataclass
class User:
    user_id: int
    username: str | None = None
    full_name: str | None = None
    language: str = UserLanguage.default().value
    role: str = UserRole.USER.value
    is_banned: bool = False
    ban_reason: str | None = None
    joined_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_active_at: str | None = None
    subscribed_channels_checked: bool = False
    ai_requests_today: int = 0
    ai_requests_reset_at: str | None = None
    notifications_enabled: bool = True  # Sozlamalar: yangi qism/bildirishnoma xabarlari
    preferred_quality: str | None = None  # oxirgi tanlangan video sifati

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    @property
    def is_admin(self) -> bool:
        return self.role in (UserRole.ADMIN.value, UserRole.MAIN_ADMIN.value)

    @property
    def is_main_admin(self) -> bool:
        return self.role == UserRole.MAIN_ADMIN.value

    def touch(self) -> None:
        """Oxirgi faollik vaqtini yangilaydi."""

        self.last_active_at = datetime.now(timezone.utc).isoformat()
