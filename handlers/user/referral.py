"""👥 Referral tizimi (#15)."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_referral")


@router.message(F.text.in_(all_variants("btn_referral")))
async def show_referral(message: Message, bot: Bot, container: Container, db_user: User) -> None:
    me = await bot.get_me()
    link = container.referral_service.build_referral_link(me.username, db_user.user_id)
    count = await container.referral_service.count_referrals(db_user.user_id)

    rows = [[InlineKeyboardButton(text="🏅 Reyting", callback_data="refleaderboard")]]
    await message.answer(
        t("referral_text", db_user.language, link=link, count=count),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data == "refleaderboard")
async def show_referral_leaderboard(callback: CallbackQuery, container: Container) -> None:
    top = await container.referral_service.leaderboard(limit=10)
    if not top:
        await callback.answer("Hozircha hech kim yo'q.", show_alert=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏅 <b>Eng ko'p taklif qilganlar:</b>\n"]
    for i, (referrer_id, count) in enumerate(top):
        user = await container.users.get_by_id(referrer_id)
        name = (user.full_name or user.username or str(referrer_id)) if user else str(referrer_id)
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {count} ta taklif")

    await callback.message.answer("\n".join(lines))
    await callback.answer()
