"""Promo-kod yaratish/ishlatish logikasi (#16, #17, #18, #19)."""

from __future__ import annotations

import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from config.enums import PromoCodeType, VipStatus
from database.models.promo import PromoCode
from database.models.vip import VipSubscription
from database.repositories.economy_repository import EconomyRepository
from database.repositories.promo_repository import PromoRepository
from database.repositories.vip_repository import VipRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class PromoRedeemError(Exception):
    """Promo-kod ishlatib bo'lmadi (mavjud emas / tugagan / limitga yetgan)."""


class PromoService:
    def __init__(
        self, promos: PromoRepository, vips: VipRepository, economy: EconomyRepository
    ) -> None:
        self._promos = promos
        self._vips = vips
        self._economy = economy

    @staticmethod
    def _generate_code(length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(random.choices(alphabet, k=length))

    async def create_code(
        self,
        promo_type: PromoCodeType,
        value: int,
        created_by: int,
        max_uses: int = 1,
        expires_in_days: int | None = None,
        custom_code: str | None = None,
    ) -> PromoCode:
        """#19 Admin Coupon Generator — yangi promo-kod yaratadi."""

        expires_at = None
        if expires_in_days:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            ).isoformat()

        if custom_code:
            code = custom_code.strip().upper()
            promo = PromoCode(
                code=code,
                type=promo_type.value,
                value=value,
                max_uses=max_uses,
                created_by=created_by,
                expires_at=expires_at,
            )
            saved, added = await self._promos.add_if_absent(promo)
            if not added:
                raise PromoRedeemError(f"'{code}' kodi allaqachon band. Boshqa kod tanlang.")
            logger.info("Promo-kod yaratildi: %s (%s, %s ta)", code, promo_type.value, value)
            return saved

        # Tasodifiy kod: to'qnashuv nazariy jihatdan mumkin bo'lgani uchun
        # ``add_if_absent`` orqali atomik urinish, kerak bo'lsa qayta
        # generatsiya bilan bir necha marta takrorlanadi.
        for _attempt in range(5):
            code = self._generate_code()
            promo = PromoCode(
                code=code,
                type=promo_type.value,
                value=value,
                max_uses=max_uses,
                created_by=created_by,
                expires_at=expires_at,
            )
            saved, added = await self._promos.add_if_absent(promo)
            if added:
                logger.info("Promo-kod yaratildi: %s (%s, %s ta)", code, promo_type.value, value)
                return saved

        raise PromoRedeemError("Noyob promo-kod generatsiya qilib bo'lmadi. Qaytadan urinib ko'ring.")

    async def redeem(self, user_id: int, code: str) -> tuple[PromoCode, str]:
        """Kodni ishlatadi va mukofotni beradi.

        Qaytaradi: ``(promo, mukofot_tavsifi)``. Muvaffaqiyatsiz bo'lsa
        ``PromoRedeemError`` ko'taradi.
        """

        code = code.strip().upper()
        existing = await self._promos.get_by_code(code)
        if existing is None:
            raise PromoRedeemError("Bunday promo-kod topilmadi.")
        if not existing.is_usable():
            raise PromoRedeemError("Bu promo-kod muddati tugagan yoki limitga yetgan.")
        if user_id in existing.used_by:
            raise PromoRedeemError("Siz bu kodni allaqachon ishlatgansiz.")

        promo = await self._promos.redeem(code, user_id)
        if promo is None:
            raise PromoRedeemError("Bu promo-kodni ishlatib bo'lmadi.")

        promo_type = PromoCodeType(promo.type)
        if promo_type == PromoCodeType.VIP_DAYS:
            await self._grant_vip_days(user_id, promo.value)
            description = f"💎 {promo.value} kunlik VIP obuna"
        else:
            profile = await self._economy.get(user_id)
            profile.coins += promo.value
            await self._economy.save(profile)
            description = f"💰 {promo.value} tanga"

        return promo, description

    async def _grant_vip_days(self, user_id: int, days: int) -> VipSubscription:
        """#17 Gift VIP — admin/promo orqali to'g'ridan-to'g'ri VIP kunlarini
        beradi (to'lovsiz). Agar faol VIP mavjud bo'lsa, muddatiga qo'shiladi.
        """

        active = await self._vips.get_active_for_user(user_id)
        now = datetime.now(timezone.utc)

        if active:
            new_expiry = datetime.fromisoformat(active.expires_at) + timedelta(days=days)
            await self._vips.update(active.id, {"expires_at": new_expiry.isoformat()})
            return active

        sub = VipSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan="gift",
            status=VipStatus.APPROVED.value,
            price=0,
            starts_at=now.isoformat(),
            expires_at=(now + timedelta(days=days)).isoformat(),
            decided_at=now.isoformat(),
        )
        await self._vips.add(sub)
        return sub

    async def gift_vip(self, admin_id: int, user_id: int, days: int) -> VipSubscription:
        """#17 Gift VIP — admin panel orqali to'g'ridan-to'g'ri chaqiriladi."""

        logger.info("Admin %s userga %s kun VIP sovg'a qildi: %s", admin_id, days, user_id)
        return await self._grant_vip_days(user_id, days)

    async def list_active_codes(self) -> list[PromoCode]:
        all_codes = await self._promos.all()
        return [c for c in all_codes if c.is_usable()]
