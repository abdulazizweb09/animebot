"""🎁 Kunlik bonus, 🏆 Yutuqlar, 🏅 Reyting — #12, #13, #14, #47, #48-50."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.badges import ALL_BADGES
from container import Container
from database.models.user import User
from services.economy_service import DailyAlreadyClaimedError
from utils.i18n import all_variants, t

router = Router(name="user_economy")


@router.message(F.text.in_(all_variants("btn_daily")))
async def claim_daily(message: Message, container: Container, db_user: User) -> None:
    try:
        profile, coins, xp = await container.economy_service.claim_daily(db_user.user_id)
    except DailyAlreadyClaimedError as exc:
        next_time = exc.next_claim_at.strftime("%Y-%m-%d %H:%M UTC")
        await message.answer(
            t("daily_already_claimed", db_user.language, next_time=next_time)
        )
        return

    await message.answer(
        t(
            "daily_claimed",
            db_user.language,
            coins=coins,
            xp=xp,
            streak=profile.login_streak,
        )
    )


@router.message(F.text.in_(all_variants("btn_achievements")))
async def show_achievements(message: Message, container: Container, db_user: User) -> None:
    from config.badges import EPISODE_MILESTONES

    earned = await container.achievement_service.list_for_user(db_user.user_id)

    lines = []
    if earned:
        lines.append(t("achievements_title", db_user.language))
        for a in earned:
            badge = ALL_BADGES.get(a.badge_code)
            if badge:
                lines.append(f"  • {badge.label} — {badge.description}")
    else:
        lines.append(t("achievements_empty", db_user.language))

    # Keyingi epizod-badge'gacha qancha qolganini ko'rsatamiz — bu
    # foydalanuvchini ko'proq ko'rishga undaydi (gamification).
    economy = await container.economy_service.get_profile(db_user.user_id)
    watched = economy.total_episodes_watched
    next_milestone = next((m for m in sorted(EPISODE_MILESTONES) if m > watched), None)
    if next_milestone:
        remaining = next_milestone - watched
        badge = EPISODE_MILESTONES[next_milestone]
        lines.append(
            f"\n📈 Keyingi yutuq: {badge.label} — yana {remaining} ta epizod ko'ring!"
        )

    await message.answer("\n".join(lines))


def _leaderboard_switch_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="✨ XP bo'yicha", callback_data="lb:xp"),
            InlineKeyboardButton(text="🏆 Yutuqlar bo'yicha", callback_data="lb:achievements"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_leaderboard")))
async def show_leaderboard(message: Message, container: Container, db_user: User) -> None:
    top = await container.economy_service.leaderboard(by="xp", limit=10)
    if not top:
        await message.answer(t("not_found", db_user.language))
        return

    lines = [t("leaderboard_title", db_user.language)]
    medals = ["🥇", "🥈", "🥉"]
    for i, profile in enumerate(top):
        user = await container.users.get_by_id(profile.user_id)
        name = (user.full_name or user.username or str(profile.user_id)) if user else str(profile.user_id)
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {profile.xp} XP (daraja {profile.level})")

    await message.answer("\n".join(lines), reply_markup=_leaderboard_switch_keyboard())


@router.callback_query(F.data == "lb:xp")
async def switch_to_xp_leaderboard(callback: CallbackQuery, container: Container) -> None:
    top = await container.economy_service.leaderboard(by="xp", limit=10)
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏅 TOP-10 (XP bo'yicha):"]
    for i, profile in enumerate(top):
        user = await container.users.get_by_id(profile.user_id)
        name = (user.full_name or user.username or str(profile.user_id)) if user else str(profile.user_id)
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {profile.xp} XP (daraja {profile.level})")

    await callback.message.edit_text("\n".join(lines), reply_markup=_leaderboard_switch_keyboard())
    await callback.answer()


@router.callback_query(F.data == "lb:achievements")
async def switch_to_achievement_leaderboard(callback: CallbackQuery, container: Container) -> None:
    top = await container.achievement_service.leaderboard(limit=10)
    if not top:
        await callback.answer("Hozircha hech kim yo'q.", show_alert=True)
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 TOP-10 (Yutuqlar bo'yicha):"]
    for i, (user_id, count) in enumerate(top):
        user = await container.users.get_by_id(user_id)
        name = (user.full_name or user.username or str(user_id)) if user else str(user_id)
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {count} ta yutuq")

    await callback.message.edit_text("\n".join(lines), reply_markup=_leaderboard_switch_keyboard())
    await callback.answer()
