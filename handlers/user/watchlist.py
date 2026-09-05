"""📌 Ro'yxatlarim (Bookmark Folder) va ▶️ Davom etish (Continue Watching)
— #9, #10, #11, #53.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.enums import WatchStatus
from container import Container
from database.models.user import User
from keyboards.user.anime_card import watch_status_keyboard
from keyboards.user.anime_list import anime_list_keyboard
from states.user_states import ManualProgressStates
from utils.i18n import all_variants

router = Router(name="user_watchlist")


def _folders_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=status.label_uz, callback_data=f"wl:folder:{status.value}")]
        for status in WatchStatus
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_watchlist")))
async def show_watchlist_menu(message: Message) -> None:
    await message.answer("📌 Ro'yxatingizni tanlang:", reply_markup=_folders_menu_keyboard())


@router.message(F.text.in_(all_variants("btn_continue_watching")))
async def show_continue_watching(message: Message, container: Container, db_user: User) -> None:
    animes = await container.watchlist_service.continue_watching(db_user.user_id)
    if not animes:
        await message.answer("▶️ Hozircha davom ettirilayotgan anime yo'q.")
        return

    codes = [a.code for a in animes]
    container.list_cache.set(db_user.user_id, "continue", codes)

    lines = ["▶️ Davom etish:"]
    for anime in animes:
        progress = await container.watchlist_service.progress_text(db_user.user_id, anime.code)
        lines.append(f"  • {anime.title_uz}" + (f" ({progress})" if progress else ""))

    await message.answer(
        "\n".join(lines),
        reply_markup=anime_list_keyboard(animes, context="continue", page=1),
    )


@router.callback_query(F.data.startswith("wl:folder:"))
async def show_folder(callback: CallbackQuery, container: Container, db_user: User) -> None:
    status_value = callback.data.split(":", 2)[2]
    status = WatchStatus(status_value)

    entries = await container.watchlist_service.list_folder(db_user.user_id, status)
    if not entries:
        await callback.answer("Bu ro'yxat bo'sh.", show_alert=True)
        return

    animes = []
    for entry in entries:
        anime = await container.animes.get_by_code(entry.anime_code)
        if anime:
            animes.append(anime)

    codes = [a.code for a in animes]
    context = f"wlf:{status.value}"
    container.list_cache.set(db_user.user_id, context, codes)

    await callback.message.answer(
        f"{status.label_uz} ({len(animes)}):",
        reply_markup=anime_list_keyboard(animes, context=context, page=1),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wl:menu:"))
async def show_status_menu(callback: CallbackQuery) -> None:
    anime_code = callback.data.split(":", 2)[2]
    await callback.message.answer(
        "📌 Bu animeni qaysi ro'yxatga qo'shamiz?",
        reply_markup=watch_status_keyboard(anime_code),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wl:set:"))
async def set_status(callback: CallbackQuery, container: Container, db_user: User) -> None:
    _, _, anime_code, status_value = callback.data.split(":")
    status = WatchStatus(status_value)

    await container.watchlist_service.set_status(db_user.user_id, anime_code, status)
    await callback.answer(f"✅ {status.label_uz} ro'yxatiga qo'shildi.")


@router.callback_query(F.data.startswith("pg:continue:"))
async def paginate_continue(callback: CallbackQuery, container: Container, db_user: User) -> None:
    page = int(callback.data.split(":")[-1])
    codes = container.list_cache.get(db_user.user_id, "continue") or []
    animes = []
    for code in codes:
        anime = await container.animes.get_by_code(code)
        if anime:
            animes.append(anime)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context="continue", page=page)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("pg:wlf:"))
async def paginate_folder(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    status_value = parts[2]
    page = int(parts[3])
    context = f"wlf:{status_value}"

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


# ---------------------------------------------------------------------------
# ✍️ Progressni qo'lda belgilash (masalan, boshqa joyda ko'rgan userlar uchun)
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("wl:setprogress:"))
async def ask_manual_progress(callback: CallbackQuery, state: FSMContext, container: Container) -> None:
    anime_code = callback.data.split(":", 2)[2]
    episodes = await container.anime_service.get_episodes(anime_code)

    await state.update_data(progress_anime_code=anime_code)
    await state.set_state(ManualProgressStates.waiting_episode_number)

    total_hint = f" (jami {len(episodes)} ta qism mavjud)" if episodes else ""
    await callback.message.answer(
        f"✍️ Nechinchi qismgacha ko'rib bo'lgansiz? Raqamni kiriting{total_hint}:"
    )
    await callback.answer()


@router.message(ManualProgressStates.waiting_episode_number, F.text)
async def save_manual_progress(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqam kiriting:")
        return

    data = await state.get_data()
    anime_code = data.get("progress_anime_code")
    await state.clear()

    if not anime_code:
        return

    episode_number = int(message.text.strip())
    await container.watchlist_service.record_progress(db_user.user_id, anime_code, episode_number)

    progress_text = await container.watchlist_service.progress_text(db_user.user_id, anime_code)
    await message.answer(f"✅ Progress yangilandi: {progress_text} qism")
