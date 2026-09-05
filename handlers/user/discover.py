"""🔥 Kashf qilish: Trending / Most Watched / Top Rated / Recently Added-Updated."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.constants import CONSTANTS
from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from utils.i18n import all_variants, t

router = Router(name="user_discover")

_DISCOVER_LIMIT = CONSTANTS.ANIME_PER_PAGE * 4  # bir nechta sahifaga yetadigan miqdor

_SECTION_TRENDING_24H = "disc:trend24"
_SECTION_TRENDING_7D = "disc:trend7d"
_SECTION_TRENDING_30D = "disc:trend30d"
_SECTION_MOST_WATCHED = "disc:most_watched"
_SECTION_TOP_RATED = "disc:top_rated"
_SECTION_RECENT_ADDED = "disc:recent_added"
_SECTION_RECENT_UPDATED = "disc:recent_updated"


def _discover_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("discover_trending", language), callback_data=_SECTION_TRENDING_24H)],
        [InlineKeyboardButton(text=t("discover_trending_week", language), callback_data=_SECTION_TRENDING_7D)],
        [InlineKeyboardButton(text=t("discover_trending_month", language), callback_data=_SECTION_TRENDING_30D)],
        [InlineKeyboardButton(text=t("discover_most_watched", language), callback_data=_SECTION_MOST_WATCHED)],
        [InlineKeyboardButton(text=t("discover_top_rated", language), callback_data=_SECTION_TOP_RATED)],
        [InlineKeyboardButton(text=t("discover_recently_added", language), callback_data=_SECTION_RECENT_ADDED)],
        [InlineKeyboardButton(text=t("discover_recently_updated", language), callback_data=_SECTION_RECENT_UPDATED)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_discover")))
async def show_discover_menu(message: Message, db_user: User) -> None:
    await message.answer(
        t("discover_menu_title", db_user.language),
        reply_markup=_discover_menu_keyboard(db_user.language),
    )


async def _send_anime_section(
    callback: CallbackQuery, container: Container, db_user: User, title: str, animes: list
) -> None:
    if not animes:
        await callback.answer(t("not_found", db_user.language), show_alert=True)
        return

    codes = [a.code for a in animes]
    context = f"disc:{callback.data.split(':', 1)[1]}"
    container.list_cache.set(db_user.user_id, context, codes)

    await callback.message.answer(
        title, reply_markup=anime_list_keyboard(animes, context=context, page=1)
    )
    await callback.answer()


@router.callback_query(F.data == _SECTION_TRENDING_24H)
async def trending_24h(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.trending(hours=24, limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "🔥 Trend (24 soat):", animes)


@router.callback_query(F.data == _SECTION_TRENDING_7D)
async def trending_7d(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.trending(hours=24 * 7, limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "🔥 Trend (7 kun):", animes)


@router.callback_query(F.data == _SECTION_TRENDING_30D)
async def trending_30d(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.trending(hours=24 * 30, limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "🔥 Trend (30 kun):", animes)


@router.callback_query(F.data == _SECTION_MOST_WATCHED)
async def most_watched(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.most_watched(limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "👁 Eng ko'p ko'rilgan:", animes)


@router.callback_query(F.data == _SECTION_TOP_RATED)
async def top_rated(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.top_rated(limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "⭐️ Eng yuqori baholangan:", animes)


@router.callback_query(F.data == _SECTION_RECENT_ADDED)
async def recently_added(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.recently_added(limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "🆕 Yangi qo'shilganlar:", animes)


@router.callback_query(F.data == _SECTION_RECENT_UPDATED)
async def recently_updated(callback: CallbackQuery, container: Container, db_user: User) -> None:
    animes = await container.anime_service.recently_updated(limit=_DISCOVER_LIMIT)
    await _send_anime_section(callback, container, db_user, "♻️ Yangilanganlar:", animes)


@router.callback_query(F.data.startswith("pg:disc:"))
async def paginate_discover(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    context = f"disc:{parts[2]}"
    page = int(parts[3])

    codes = container.list_cache.get(db_user.user_id, context) or []
    animes = []
    for code in codes:
        anime = await container.animes.get_by_code(code)
        if anime:
            animes.append(anime)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context=context, page=page)
        )
    await callback.answer()
