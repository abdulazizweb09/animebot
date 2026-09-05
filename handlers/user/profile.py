"""👤 Profil bo'limi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_profile")


@router.message(F.text.in_(all_variants("btn_profile")))
async def show_profile(message: Message, container: Container, db_user: User) -> None:
    vip = await container.vips.get_active_for_user(db_user.user_id)
    vip_status = (
        t("vip_active", db_user.language, expires_at=vip.expires_at[:10])
        if vip
        else t("vip_inactive", db_user.language)
    )

    text = t(
        "profile_text",
        db_user.language,
        user_id=db_user.user_id,
        full_name=db_user.full_name or "-",
        lang_label=db_user.language.upper(),
        role=db_user.role,
        vip_status=vip_status,
        joined_at=db_user.joined_at[:10],
    )

    economy = await container.economy_service.get_profile(db_user.user_id)
    text += t(
        "economy_profile_line",
        db_user.language,
        coins=economy.coins,
        xp=economy.xp,
        level=economy.level,
    )

    tier, total_vip_days, days_to_next = await container.vip_service.get_tier_progress(db_user.user_id)
    if tier.value != "none":
        text += f"\n🌟 Loyallik darajasi: {tier.label} (jami {total_vip_days} kun VIP)"
        if days_to_next:
            next_tier_names = {"bronze": "Silver", "silver": "Gold"}
            next_name = next_tier_names.get(tier.value, "")
            text += f"\n📈 Keyingi darajagacha ({next_name}): {days_to_next} kun qoldi"

    await message.answer(text)
