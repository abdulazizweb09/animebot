"""VIP obuna so'rovlari va tasdiqlash/rad etish logikasi."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from config.enums import VipPlan, VipStatus, VipTier
from config.settings import Settings
from database.models.vip import VipSubscription
from database.repositories.vip_repository import VipRepository
from utils.exceptions import VipAlreadyActiveError
from utils.logger import get_logger

logger = get_logger(__name__)


class VipService:
    def __init__(self, vips: VipRepository, settings: Settings) -> None:
        self._vips = vips
        self._settings = settings

    async def request_plan(
        self, user_id: int, plan: VipPlan, receipt_file_id: str | None
    ) -> VipSubscription:
        """Eslatma: bu yerda ``get_pending_for_user`` + ``hard_delete`` +
        ``add`` ketma-ketligi to'liq atomik emas (nazariy jihatdan, foydalanuvchi
        millisekundlar ichida ikki marta chek yuborsa, ikkita "pending" yozuv
        qolishi mumkin). Lekin ``VipSubscription.id`` UUID bo'lgani uchun bu
        ma'lumotlar buzilishiga OLIB KELMAYDI — faqat admin panelda bitta
        o'rniga ikkita so'rov ko'rinishi mumkin, bu esa admin tomonidan
        oddiy tarzda hal qilinadi. Shu sabab bu yerga qo'shimcha lock
        qo'shilmadi (murakkablik/foyda nisbati past).
        """

        active = await self._vips.get_active_for_user(user_id)
        if active:
            raise VipAlreadyActiveError(
                f"Foydalanuvchi {user_id} allaqachon faol VIP obunaga ega."
            )

        pending = await self._vips.get_pending_for_user(user_id)
        if pending:
            await self._vips.hard_delete(pending.id)

        sub = VipSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan=plan.value,
            status=VipStatus.PENDING.value,
            price=self._settings.vip_pricing.price_for(plan),
            receipt_file_id=receipt_file_id,
        )
        await self._vips.add(sub)
        logger.info("Yangi VIP so'rov: user=%s plan=%s", user_id, plan.value)
        return sub

    async def approve(self, sub_id: str, admin_id: int) -> VipSubscription | None:
        sub = await self._vips.get(sub_id)
        if sub is None:
            return None

        plan = VipPlan(sub.plan)
        now = datetime.now(timezone.utc)
        starts_at = now
        expires_at = now + timedelta(days=plan.days)

        return await self._vips.update(
            sub_id,
            {
                "status": VipStatus.APPROVED.value,
                "decided_at": now.isoformat(),
                "decided_by": admin_id,
                "starts_at": starts_at.isoformat(),
                "expires_at": expires_at.isoformat(),
            },
        )

    async def reject(self, sub_id: str, admin_id: int, reason: str) -> VipSubscription | None:
        return await self._vips.update(
            sub_id,
            {
                "status": VipStatus.REJECTED.value,
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "decided_by": admin_id,
                "reject_reason": reason,
            },
        )

    async def get_active(self, user_id: int) -> VipSubscription | None:
        return await self._vips.get_active_for_user(user_id)

    async def list_pending(self) -> list[VipSubscription]:
        return await self._vips.list_pending()

    async def mark_expired(self) -> list[VipSubscription]:
        """Muddati o'tgan obunalarni "expired" deb belgilaydi. Cron/job uchun."""

        expired = await self._vips.list_expired_unmarked()
        for sub in expired:
            await self._vips.update(sub.id, {"status": VipStatus.EXPIRED.value})
        if expired:
            logger.info("%d ta VIP obuna muddati tugagan deb belgilandi.", len(expired))
        return expired

    async def list_expiring_soon(self, days: int = 3) -> list[VipSubscription]:
        return await self._vips.list_expiring_within(days)

    async def get_tier(self, user_id: int) -> VipTier:
        """#VIP Tier — umrbod olingan VIP kunlar yig'indisiga qarab
        Bronze/Silver/Gold darajasini aniqlaydi."""

        total_days = await self._vips.cumulative_vip_days(user_id)
        return VipTier.for_cumulative_days(total_days)

    async def get_tier_progress(self, user_id: int) -> tuple[VipTier, int, int | None]:
        """Joriy daraja, umrbod kunlar va keyingi darajagacha qolgan kunlar
        sonini qaytaradi. Eng yuqori daraja (Gold) uchun uchinchi qiymat
        ``None`` bo'ladi.
        """

        total_days = await self._vips.cumulative_vip_days(user_id)
        tier = VipTier.for_cumulative_days(total_days)

        thresholds = {VipTier.NONE: 1, VipTier.BRONZE: 90, VipTier.SILVER: 365}
        next_threshold = thresholds.get(tier)
        remaining = (next_threshold - total_days) if next_threshold else None
        return tier, total_days, remaining
