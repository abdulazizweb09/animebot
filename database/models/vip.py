"""VIP obuna modeli."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from config.enums import VipPlan, VipStatus


@dataclass
class VipSubscription:
    id: str  # uuid
    user_id: int
    plan: str = VipPlan.ONE_MONTH.value
    status: str = VipStatus.PENDING.value
    price: int = 0
    receipt_file_id: str | None = None
    requested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    decided_at: str | None = None
    decided_by: int | None = None
    reject_reason: str | None = None
    starts_at: str | None = None
    expires_at: str | None = None
    warned_days: list[int] = field(default_factory=list)  # allaqachon eslatilgan kunlar

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VipSubscription":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def is_active(self) -> bool:
        if self.status != VipStatus.APPROVED.value or not self.expires_at:
            return False
        expires = datetime.fromisoformat(self.expires_at)
        return expires > datetime.now(timezone.utc)
