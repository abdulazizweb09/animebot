"""🧑‍🎤 Character Search (#25) va Voice Actor Search (#26)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from container import Container
from database.models.user import User
from states.user_states import CharacterSearchStates
from utils.i18n import all_variants, t

router = Router(name="user_character_search")


@router.message(F.text.in_(all_variants("btn_character_search")))
async def ask_character_query(message: Message, state: FSMContext, db_user: User) -> None:
    await state.set_state(CharacterSearchStates.waiting_query)
    await message.answer(t("character_ask_name", db_user.language))


@router.message(CharacterSearchStates.waiting_query, F.text)
async def run_character_search(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    query = message.text.strip()
    await state.clear()

    by_name = await container.character_service.search_by_name(query)
    by_actor = await container.character_service.search_by_voice_actor(query)

    seen_ids = set()
    results = []
    for c in by_name + by_actor:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            results.append(c)

    if not results:
        await message.answer(t("not_found", db_user.language))
        return

    lines = []
    for c in results[:15]:
        anime = await container.animes.get_by_code(c.anime_code)
        anime_title = anime.title_uz if anime else c.anime_code
        va_part = f" (ovoz: {c.voice_actor})" if c.voice_actor else ""
        lines.append(f"🧑‍🎤 <b>{c.name}</b>{va_part} — {anime_title}")

    await message.answer("\n".join(lines))
