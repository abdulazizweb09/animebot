"""Promo-kod modeli — #16 Promo Code, #17 Gift VIP, #18 VIP Coupon."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PromoCode:
    code: str  # noyob kod (masalan "WELCOME2026")
    type: str  # "vip_days" | "coins"
    value: int  # vip_days uchun kunlar soni, coins uchun tanga miqdori
    max_uses: int = 1
    used_count: int = 0
    used_by: list[int] = field(default_factory=list)
    is_active: bool = True
    created_by: int | None = None
    expires_at: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromoCode":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def is_usable(self) -> bool:
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at:
            if datetime.now(timezone.utc) > datetime.fromisoformat(self.expires_at):
                return False
        return True
