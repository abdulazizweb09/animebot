"""⭐️ Sevimlilar bo'limi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config.constants import CONSTANTS
from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from utils.i18n import all_variants

router = Router(name="user_favorites")


@router.message(F.text.in_(all_variants("btn_favorites")))
async def show_favorites(message: Message, container: Container, db_user: User) -> None:
    favs = await container.favorite_service.list_for_user(db_user.user_id)
    if not favs:
        await message.answer("⭐️ Sevimlilar ro'yxati bo'sh.")
        return

    animes = []
    for fav in favs:
        anime = await container.animes.get_by_code(fav.anime_code)
        if anime:
            animes.append(anime)

    codes = [a.code for a in animes]
    container.list_cache.set(db_user.user_id, "favorites", codes)

    await message.answer(
        f"⭐️ Sevimlilar ({len(animes)}):",
        reply_markup=anime_list_keyboard(animes, context="favorites", page=1),
    )


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_PAGE}:favorites:"))
async def paginate_favorites(callback: CallbackQuery, container: Container, db_user: User) -> None:
    page = int(callback.data.split(":")[-1])
    codes = container.list_cache.get(db_user.user_id, "favorites") or []
    animes = []
    for code in codes:
        anime = await container.animes.get_by_code(code)
        if anime:
            animes.append(anime)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context="favorites", page=page)
        )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_FAV}:"))
async def toggle_favorite(callback: CallbackQuery, container: Container, db_user: User) -> None:
    anime_code = callback.data.split(":", 1)[1]
    now_favorite = await container.favorite_service.toggle(db_user.user_id, anime_code)
    await container.analytics_service.log_event(
        "favorite_add" if now_favorite else "favorite_remove",
        user_id=db_user.user_id,
        anime_code=anime_code,
    )
    text = "❤️ Sevimlilarga qo'shildi" if now_favorite else "💔 Sevimlilardan olib tashlandi"
    await callback.answer(text)
