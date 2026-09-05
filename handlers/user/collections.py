"""🎞 Anime Collection / Franchise — foydalanuvchi tomoni."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from keyboards.user.collections import collections_keyboard
from utils.i18n import all_variants, t

router = Router(name="user_collections")


@router.message(F.text.in_(all_variants("btn_collections")))
async def show_collections(message: Message, container: Container, db_user: User) -> None:
    collections = await container.collection_service.list_all()
    if not collections:
        await message.answer(t("collections_empty", db_user.language))
        return

    await message.answer(
        t("collections_title", db_user.language),
        reply_markup=collections_keyboard(collections),
    )


@router.callback_query(F.data.startswith("coll:"))
async def show_collection_animes(
    callback: CallbackQuery, container: Container, db_user: User
) -> None:
    collection_id = callback.data.split(":", 1)[1]
    collection = await container.collection_service.get(collection_id)
    if collection is None:
        await callback.answer(t("not_found", db_user.language), show_alert=True)
        return

    animes = await container.collection_service.get_animes(collection_id)
    if not animes:
        await callback.answer(t("not_found", db_user.language), show_alert=True)
        return

    codes = [a.code for a in animes]
    context = f"coll:{collection_id}"
    container.list_cache.set(db_user.user_id, context, codes)

    caption = f"🎞 <b>{collection.title}</b>"
    if collection.description:
        caption += f"\n\n{collection.description}"

    rows = anime_list_keyboard(animes, context=context, page=1).inline_keyboard
    rows = list(rows) + [
        [
            InlineKeyboardButton(text="📜 Timeline", callback_data=f"colltime:{collection_id}"),
            InlineKeyboardButton(text="▶️ Watch Order", callback_data=f"collorder:{collection_id}"),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)

    if collection.poster_file_id:
        await callback.message.answer_photo(
            collection.poster_file_id, caption=caption, reply_markup=markup
        )
    else:
        await callback.message.answer(caption, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("pg:coll:"))
async def paginate_collection(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    collection_id = parts[2]
    page = int(parts[3])
    context = f"coll:{collection_id}"

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


@router.callback_query(F.data.startswith("colltime:"))
async def show_timeline(callback: CallbackQuery, container: Container) -> None:
    """#31 Anime Timeline — nashr yili bo'yicha xronologik tartib."""

    collection_id = callback.data.split(":", 1)[1]
    animes = await container.collection_service.get_animes_by_timeline(collection_id)
    if not animes:
        await callback.answer("Bo'sh", show_alert=True)
        return

    lines = ["📜 <b>Timeline</b> (nashr yili bo'yicha):\n"]
    for a in animes:
        lines.append(f"  {a.year or '—'} — {a.title_uz}")
    await callback.message.answer("\n".join(lines))
    await callback.answer()


@router.callback_query(F.data.startswith("collorder:"))
async def show_watch_order(callback: CallbackQuery, container: Container) -> None:
    """#32 Watch Order Generator, #33 Manga Order — admin belgilagan
    tartib bo'yicha (yoki yil bo'yicha, agar belgilanmagan bo'lsa)."""

    collection_id = callback.data.split(":", 1)[1]
    animes = await container.collection_service.get_animes_watch_order(collection_id)
    if not animes:
        await callback.answer("Bo'sh", show_alert=True)
        return

    lines = ["▶️ <b>Tomosha qilish tartibi</b>:\n"]
    for i, a in enumerate(animes, start=1):
        lines.append(f"  {i}. {a.title_uz} ({a.year or '—'})")
    await callback.message.answer("\n".join(lines))
    await callback.answer()
