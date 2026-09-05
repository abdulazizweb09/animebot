"""🕘 Ko'rish tarixi bo'limi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from utils.i18n import all_variants

router = Router(name="user_history")


@router.message(F.text.in_(all_variants("btn_history")))
async def show_history(message: Message, container: Container, db_user: User) -> None:
    entries = await container.history_service.list_for_user(db_user.user_id)
    if not entries:
        await message.answer("🕘 Tarix bo'sh.")
        return

    animes = []
    seen = set()
    for entry in entries:
        if entry.anime_code in seen:
            continue
        seen.add(entry.anime_code)
        anime = await container.animes.get_by_code(entry.anime_code)
        if anime:
            animes.append(anime)

    await message.answer(
        f"🕘 Oxirgi ko'rilganlar ({len(animes)}):",
        reply_markup=anime_list_keyboard(animes, context="history", page=1),
    )
