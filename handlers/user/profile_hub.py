"""👤 Profil — shaxsiy bo'lim markaziy menyusi (hub).

Talab qilingan asosiy 10 ta bo'lim: Profil, Sevimlilar, Ro'yxatlarim,
Reyting, Tanga do'koni, Yutuqlarim, Davom etish, Sozlamalar, Promo-kodlar,
Do'st taklif qilish.

Bundan tashqari, avval qurilgan boshqa funksiyalar (Tarix, Bildirishnomalar,
Yangiliklar, Viktorina/So'rovlar) "➕ Boshqa" bo'limi ostida saqlanib
qolgan — hech qanday funksiya yo'qolmagan, faqat menyu tuzilishi
soddalashtirilgan.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_profile_hub")


def _profile_hub_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="👤 Profil", callback_data="profilehub:profile")],
        [InlineKeyboardButton(text="❤️ Sevimlilar", callback_data="profilehub:favorites")],
        [InlineKeyboardButton(text="📌 Ro'yxatlarim", callback_data="profilehub:lists")],
        [InlineKeyboardButton(text="🏅 Reyting", callback_data="profilehub:leaderboard")],
        [InlineKeyboardButton(text="🛍 Tanga do'koni", callback_data="profilehub:shop")],
        [InlineKeyboardButton(text="🏆 Yutuqlarim", callback_data="profilehub:achievements")],
        [InlineKeyboardButton(text="▶️ Davom etish", callback_data="profilehub:continue")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="profilehub:settings")],
        [InlineKeyboardButton(text="🎟 Promo-kodlar", callback_data="profilehub:promo")],
        [InlineKeyboardButton(text="👥 Do'st taklif qilish", callback_data="profilehub:referral")],
        [InlineKeyboardButton(text="➕ Boshqa", callback_data="profilehub:more")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _more_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🕘 Tarix", callback_data="profilehub:history")],
        [InlineKeyboardButton(text="🔔 Bildirishnomalar", callback_data="profilehub:notifications")],
        [InlineKeyboardButton(text="📰 Yangiliklar", callback_data="profilehub:news")],
        [InlineKeyboardButton(text="🧠 Viktorina", callback_data="profilehub:quiz")],
        [InlineKeyboardButton(text="📊 So'rovlar", callback_data="profilehub:polls")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profilehub:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_profile_hub")))
async def show_profile_hub(message: Message, db_user: User) -> None:
    await message.answer(
        t("profile_hub_title", db_user.language), reply_markup=_profile_hub_keyboard()
    )


@router.callback_query(F.data == "profilehub:home")
async def back_to_profile_hub(callback: CallbackQuery, db_user: User) -> None:
    await callback.message.edit_text(
        t("profile_hub_title", db_user.language), reply_markup=_profile_hub_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "profilehub:more")
async def show_more_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("➕ Qo'shimcha bo'limlar:", reply_markup=_more_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("profilehub:"))
async def route_profile_hub(
    callback: CallbackQuery, state: FSMContext, container: Container, db_user: User
) -> None:
    action = callback.data.split(":", 1)[1]
    if action in ("home", "more"):
        return  # yuqorida alohida ishlangan
    await callback.answer()

    if action == "profile":
        from handlers.user.profile import show_profile

        await show_profile(callback.message, container, db_user)
    elif action == "favorites":
        from handlers.user.favorites import show_favorites

        await show_favorites(callback.message, container, db_user)
    elif action == "lists":
        from handlers.user.watchlist import show_watchlist_menu

        await show_watchlist_menu(callback.message)
    elif action == "leaderboard":
        from handlers.user.economy import show_leaderboard

        await show_leaderboard(callback.message, container, db_user)
    elif action == "shop":
        from handlers.user.shop import show_shop

        await show_shop(callback.message, container, db_user)
    elif action == "achievements":
        from handlers.user.economy import show_achievements

        await show_achievements(callback.message, container, db_user)
    elif action == "continue":
        from handlers.user.watchlist import show_continue_watching

        await show_continue_watching(callback.message, container, db_user)
    elif action == "settings":
        from handlers.user.settings import show_settings

        await show_settings(callback.message, db_user)
    elif action == "promo":
        from handlers.user.promo import ask_promo_code

        await ask_promo_code(callback.message, state, db_user)
    elif action == "referral":
        from handlers.user.referral import show_referral

        await show_referral(callback.message, callback.bot, container, db_user)
    elif action == "history":
        from handlers.user.history import show_history

        await show_history(callback.message, container, db_user)
    elif action == "notifications":
        from handlers.user.notifications import show_notifications

        await show_notifications(callback.message, container, db_user)
    elif action == "news":
        from handlers.user.news import show_news

        await show_news(callback.message, container, db_user)
    elif action == "quiz":
        from handlers.user.poll import start_quiz

        await start_quiz(callback.message, container, db_user)
    elif action == "polls":
        from handlers.user.poll import show_active_polls

        await show_active_polls(callback.message, container, db_user)
