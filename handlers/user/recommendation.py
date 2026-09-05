"""🎯 Anime Recommendation Engine — #3."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from utils.i18n import all_variants, t

router = Router(name="user_recommendation")


@router.message(F.text.in_(all_variants("btn_recommend")))
async def show_recommendations(message: Message, container: Container, db_user: User) -> None:
    animes = await container.recommendation_service.recommend(db_user.user_id, limit=20)
    if not animes:
        await message.answer(t("not_found", db_user.language))
        return

    codes = [a.code for a in animes]
    container.list_cache.set(db_user.user_id, "recommend", codes)

    await message.answer(
        t("recommend_title", db_user.language),
        reply_markup=anime_list_keyboard(animes, context="recommend", page=1),
    )


@router.callback_query(F.data.startswith("pg:recommend:"))
async def paginate_recommend(callback: CallbackQuery, container: Container, db_user: User) -> None:
    page = int(callback.data.split(":")[-1])
    codes = container.list_cache.get(db_user.user_id, "recommend") or []
    animes = [a for a in [await container.animes.get_by_code(c) for c in codes] if a]

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context="recommend", page=page)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("similar:"))
async def show_similar(callback: CallbackQuery, container: Container, db_user: User) -> None:
    anime_code = callback.data.split(":", 1)[1]
    animes = await container.recommendation_service.similar_to(anime_code, limit=10)
    if not animes:
        await callback.answer(t("not_found", db_user.language), show_alert=True)
        return

    codes = [a.code for a in animes]
    context = f"similar:{anime_code}"
    container.list_cache.set(db_user.user_id, context, codes)

    await callback.message.answer(
        t("similar_btn", db_user.language),
        reply_markup=anime_list_keyboard(animes, context=context, page=1),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pg:similar:"))
async def paginate_similar(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    context = f"similar:{parts[2]}"
    page = int(parts[3])

    codes = container.list_cache.get(db_user.user_id, context) or []
    animes = [a for a in [await container.animes.get_by_code(c) for c in codes] if a]

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context=context, page=page)
        )
    await callback.answer()
