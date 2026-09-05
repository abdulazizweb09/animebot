"""🗂 Kategoriyalar (janrlar) bo'yicha ko'rish."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.constants import CONSTANTS
from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from utils.i18n import all_variants

router = Router(name="user_categories")


async def _all_genres(container: Container) -> list[str]:
    animes = await container.animes.all()
    genres: set[str] = set()
    for a in animes:
        genres.update(a.genres)
    return sorted(genres)


@router.message(F.text.in_(all_variants("btn_categories")))
async def show_categories(message: Message, container: Container) -> None:
    genres = await _all_genres(container)
    if not genres:
        await message.answer("Hozircha kategoriyalar mavjud emas.")
        return

    rows = [
        [InlineKeyboardButton(text=g, callback_data=f"{CONSTANTS.CB_CATEGORY}:{g}")]
        for g in genres
    ]
    await message.answer(
        "🗂 Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_CATEGORY}:"))
async def show_category_results(
    callback: CallbackQuery, container: Container, db_user: User
) -> None:
    genre = callback.data.split(":", 1)[1]
    animes = await container.anime_service.list_by_category(genre)

    if not animes:
        await callback.answer("Bo'sh", show_alert=True)
        return

    codes = [a.code for a in animes]
    container.list_cache.set(db_user.user_id, f"cat:{genre}", codes)

    if callback.message:
        await callback.message.answer(
            f"🗂 {genre}: {len(animes)} ta natija",
            reply_markup=anime_list_keyboard(animes, context=f"cat:{genre}", page=1),
        )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_PAGE}:cat:"))
async def paginate_category(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    genre = parts[2]
    page = int(parts[3])
    context = f"cat:{genre}"

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
