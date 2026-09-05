"""🎬 Studiya bo'yicha qidiruv (#27 Studio Search)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from utils.i18n import all_variants

router = Router(name="user_studio")


@router.message(F.text.in_(all_variants("btn_studio")))
async def show_studios(message: Message, container: Container) -> None:
    studios = await container.anime_service.all_studios()
    if not studios:
        await message.answer("🎬 Hozircha studiya ma'lumotlari mavjud emas.")
        return

    rows = [
        [InlineKeyboardButton(text=s, callback_data=f"studio:{s}")] for s in studios
    ]
    await message.answer(
        "🎬 Studiyani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("studio:"))
async def show_studio_animes(callback: CallbackQuery, container: Container, db_user: User) -> None:
    studio = callback.data.split(":", 1)[1]
    animes = await container.anime_service.list_by_studio(studio)
    if not animes:
        await callback.answer("Topilmadi", show_alert=True)
        return

    codes = [a.code for a in animes]
    context = f"studio:{studio}"
    container.list_cache.set(db_user.user_id, context, codes)

    await callback.message.answer(
        f"🎬 {studio}: {len(animes)} ta anime",
        reply_markup=anime_list_keyboard(animes, context=context, page=1),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pg:studio:"))
async def paginate_studio(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    studio = parts[2]
    page = int(parts[3])
    context = f"studio:{studio}"

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
