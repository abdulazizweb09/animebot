"""🔍 Anime izlash — barcha qidiruv/kashf qilish usullarini birlashtirgan
markaziy menyu (hub).

Bu handler mavjud funksiyalarni QAYTA YOZMAYDI — ularning handler
funksiyalarini to'g'ridan-to'g'ri chaqiradi (DRY). Shu sabab bu yerda
hech qanday biznes-mantiq yo'q, faqat navigatsiya.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_search_hub")


def _search_hub_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔎 Qidirish", callback_data="searchhub:search")],
        [InlineKeyboardButton(text="🗂 Kategoriyalar", callback_data="searchhub:categories")],
        [InlineKeyboardButton(text="🔥 Kashf qilish", callback_data="searchhub:discover")],
        [InlineKeyboardButton(text="🎯 Tavsiyalar", callback_data="searchhub:recommend")],
        [InlineKeyboardButton(text="🎲 Tasodifiy anime", callback_data="searchhub:random")],
        [InlineKeyboardButton(text="🎞 Kolleksiyalar", callback_data="searchhub:collections")],
        [InlineKeyboardButton(text="🎬 Studiya", callback_data="searchhub:studio")],
        [InlineKeyboardButton(text="🧰 Kengaytirilgan filter", callback_data="searchhub:advanced")],
        [InlineKeyboardButton(text="📅 Kalendar", callback_data="searchhub:calendar")],
        [InlineKeyboardButton(text="🧑‍🎤 Personaj qidirish", callback_data="searchhub:character")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_anime_search_hub")))
async def show_search_hub(message: Message, db_user: User) -> None:
    await message.answer(
        t("search_hub_title", db_user.language), reply_markup=_search_hub_keyboard()
    )


@router.callback_query(F.data.startswith("searchhub:"))
async def route_search_hub(
    callback: CallbackQuery, state: FSMContext, container: Container, db_user: User
) -> None:
    action = callback.data.split(":", 1)[1]
    await callback.answer()

    if action == "search":
        from handlers.user.search import ask_search_query

        await ask_search_query(callback.message, state, container, db_user)
    elif action == "categories":
        from handlers.user.categories import show_categories

        await show_categories(callback.message, container)
    elif action == "discover":
        from handlers.user.discover import show_discover_menu

        await show_discover_menu(callback.message, db_user)
    elif action == "recommend":
        from handlers.user.recommendation import show_recommendations

        await show_recommendations(callback.message, container, db_user)
    elif action == "random":
        from handlers.user.random_anime import show_random_anime

        await show_random_anime(callback.message, container, db_user)
    elif action == "collections":
        from handlers.user.collections import show_collections

        await show_collections(callback.message, container, db_user)
    elif action == "studio":
        from handlers.user.studio_search import show_studios

        await show_studios(callback.message, container)
    elif action == "advanced":
        from handlers.user.advanced import show_advanced_menu

        await show_advanced_menu(callback.message, db_user)
    elif action == "calendar":
        from handlers.user.calendar import show_calendar

        await show_calendar(callback.message, container, db_user)
    elif action == "character":
        from handlers.user.character_search import ask_character_query

        await ask_character_query(callback.message, state, db_user)
