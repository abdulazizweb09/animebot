"""🔍 Qidirish oqimi, shu jumladan #23 Voice Search va #24 Image Search."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.constants import CONSTANTS
from container import Container
from database.models.anime import Anime
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from states.user_states import SearchStates
from utils.exceptions import AIServiceError
from utils.i18n import all_variants, t
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="user_search")


@router.message(F.text.in_(all_variants("btn_search")))
async def ask_search_query(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
    await state.set_state(SearchStates.waiting_query)
    prompts = {
        "uz": "🔍 Anime nomini yozing (yoki 🎙 ovozli xabar / 🖼 poster rasmi yuboring):",
        "ru": "🔍 Введите название аниме (или отправьте 🎙 голосовое / 🖼 постер):",
        "en": "🔍 Type the anime title (or send a 🎙 voice message / 🖼 poster image):",
    }
    await message.answer(prompts.get(db_user.language, prompts["uz"]))

    recent = await container.search_service.recent_searches(db_user.user_id, limit=5)
    if recent:
        rows = [
            [InlineKeyboardButton(text=f"🕘 {q}", callback_data=f"resrch:{q}")] for q in recent
        ]
        await message.answer(
            "Oxirgi qidiruvlaringiz:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
        )


@router.callback_query(SearchStates.waiting_query, F.data.startswith("resrch:"))
async def repeat_recent_search(
    callback: CallbackQuery, state: FSMContext, container: Container, db_user: User
) -> None:
    query = callback.data.split(":", 1)[1]
    await state.clear()
    await _run_search_and_reply(callback.message, container, db_user, query)
    await callback.answer()


async def _run_search_and_reply(
    message: Message, container: Container, db_user: User, query: str
) -> list[Anime]:
    results = await container.search_service.search(query, user_id=db_user.user_id)
    await container.analytics_service.log_event(
        "search", user_id=db_user.user_id, meta={"query": query, "results": len(results)}
    )
    if not results:
        await message.answer(t("not_found", db_user.language))
        return results

    codes = [a.code for a in results]
    container.list_cache.set(db_user.user_id, "search", codes)

    await message.answer(
        f"🔎 «{query}» — {len(results)} ta natija topildi:",
        reply_markup=anime_list_keyboard(results, context="search", page=1),
    )
    return results


@router.message(SearchStates.waiting_query, F.text)
async def run_search(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    query = (message.text or "").strip()
    await state.clear()
    await _run_search_and_reply(message, container, db_user, query)


# ---------------------------------------------------------------------------
# #23 Voice Search — ovozli xabar orqali qidirish
# ---------------------------------------------------------------------------


async def _handle_voice_search(message: Message, container: Container, db_user: User) -> None:
    from handlers.user.ai_assistant import require_vip_for_ai

    if not await require_vip_for_ai(message, container, db_user):
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    file = await message.bot.get_file(message.voice.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    try:
        query = await container.ai_service.transcribe_voice_search(
            file_bytes.read(), mime_type="audio/ogg"
        )
    except AIServiceError as exc:
        logger.error("Voice search xatosi: %s", exc)
        await message.answer("⚠️ Ovozli xabarni tanib bo'lmadi. Matn bilan qidirib ko'ring.")
        return

    await message.answer(f"🎙 Tanildi: «{query}»")
    await _run_search_and_reply(message, container, db_user, query)


@router.message(SearchStates.waiting_query, F.voice)
async def voice_search_in_state(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
    await state.clear()
    await _handle_voice_search(message, container, db_user)


@router.message(StateFilter(None), F.voice)
async def voice_search_global(message: Message, container: Container, db_user: User) -> None:
    """Foydalanuvchi "🔍 Qidirish" tugmasini bosmasdan ham, istalgan
    paytda ovozli xabar yuborib qidira oladi (agar boshqa FSM oqimida
    bo'lmasa)."""

    await _handle_voice_search(message, container, db_user)


# ---------------------------------------------------------------------------
# #24 Image Search — poster rasmi orqali qidirish
# ---------------------------------------------------------------------------


async def _handle_image_search(message: Message, container: Container, db_user: User) -> None:
    from handlers.user.ai_assistant import require_vip_for_ai

    if not await require_vip_for_ai(message, container, db_user):
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    file = await message.bot.get_file(message.photo[-1].file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    try:
        guess = await container.ai_service.identify_anime_from_image(
            file_bytes.read(), mime_type="image/jpeg"
        )
    except AIServiceError as exc:
        logger.error("Image search xatosi: %s", exc)
        await message.answer("⚠️ Rasmni tanib bo'lmadi. Matn bilan qidirib ko'ring.")
        return

    await message.answer(f"🖼 Taxmin qilindi: «{guess}»")
    await _run_search_and_reply(message, container, db_user, guess)


@router.message(SearchStates.waiting_query, F.photo)
async def image_search_in_state(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
    await state.clear()
    await _handle_image_search(message, container, db_user)


@router.message(StateFilter(None), F.photo)
async def image_search_global(message: Message, container: Container, db_user: User) -> None:
    """Foydalanuvchi istalgan paytda poster/skrinshot yuborib, anime
    nomini aniqlashi mumkin (agar boshqa FSM oqimida bo'lmasa)."""

    await _handle_image_search(message, container, db_user)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_PAGE}:search:"))
async def paginate_search(callback: CallbackQuery, container: Container, db_user: User) -> None:
    page = int(callback.data.split(":")[-1])
    codes = container.list_cache.get(db_user.user_id, "search") or []
    animes = []
    for code in codes:
        anime = await container.animes.get_by_code(code)
        if anime:
            animes.append(anime)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context="search", page=page)
        )
    await callback.answer()
