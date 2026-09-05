"""🎲 Tasodifiy anime — "nima ko'raman" degan tanlov muammosini hal qiladi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from container import Container
from database.models.user import User
from handlers.user.anime_detail import send_anime_card
from utils.i18n import all_variants, t

router = Router(name="user_random_anime")


@router.message(F.text.in_(all_variants("btn_random")))
async def show_random_anime(message: Message, container: Container, db_user: User) -> None:
    # Foydalanuvchi allaqachon ko'rgan animelarni imkon qadar chetlab
    # o'tamiz — shunda haqiqatan ham "yangi" narsa tavsiya qilinadi.
    history = await container.history.list_for_user(db_user.user_id, limit=10000)
    watched_codes = {h.anime_code for h in history}

    anime = await container.anime_service.random_one(exclude_codes=watched_codes)
    if anime is None:
        await message.answer(t("not_found", db_user.language))
        return

    sent = await send_anime_card(message, container, db_user, anime, record_view=False)
    if not sent:
        # VIP-only chiqib qoldi — oddiy (VIP bo'lmagan) anime bilan qayta urinamiz
        anime = await container.anime_service.random_one(
            exclude_codes=watched_codes | {anime.code}
        )
        if anime:
            await send_anime_card(message, container, db_user, anime, record_view=False)
        else:
            await message.answer(t("not_found", db_user.language))
