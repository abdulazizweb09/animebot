"""🧰 Kengaytirilgan bo'lim: Turlar (#37-39), Advanced Filter (#29),
Anime Compare (#30).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.enums import AnimeType
from container import Container
from database.models.user import User
from keyboards.user.anime_list import anime_list_keyboard
from states.user_states import CompareStates, FilterStates
from utils.i18n import all_variants, t

router = Router(name="user_advanced")

_MENU_TYPES = "adv:menu:types"
_MENU_FILTER = "adv:menu:filter"
_MENU_COMPARE = "adv:menu:compare"


def _advanced_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("adv_types", language), callback_data=_MENU_TYPES)],
        [InlineKeyboardButton(text=t("adv_filter", language), callback_data=_MENU_FILTER)],
        [InlineKeyboardButton(text=t("adv_compare", language), callback_data=_MENU_COMPARE)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_advanced")))
async def show_advanced_menu(message: Message, db_user: User) -> None:
    await message.answer(
        t("advanced_menu_title", db_user.language),
        reply_markup=_advanced_menu_keyboard(db_user.language),
    )


# ---------------------------------------------------------------------------
# #37-39 Movie / OVA / Special / TV List
# ---------------------------------------------------------------------------


@router.callback_query(F.data == _MENU_TYPES)
async def show_type_menu(callback: CallbackQuery) -> None:
    rows = [
        [InlineKeyboardButton(text=t_.label_uz, callback_data=f"adv:type:{t_.value}")]
        for t_ in AnimeType
    ]
    await callback.message.answer(
        "📼 Turni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adv:type:"))
async def show_type_results(callback: CallbackQuery, container: Container, db_user: User) -> None:
    type_value = callback.data.split(":", 2)[2]
    animes = await container.anime_service.list_by_type(type_value)
    if not animes:
        await callback.answer(t("not_found", db_user.language), show_alert=True)
        return

    codes = [a.code for a in animes]
    context = f"advtype:{type_value}"
    container.list_cache.set(db_user.user_id, context, codes)

    await callback.message.answer(
        f"📼 {len(animes)} ta natija:",
        reply_markup=anime_list_keyboard(animes, context=context, page=1),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pg:advtype:"))
async def paginate_type(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    context = f"advtype:{parts[2]}"
    page = int(parts[3])

    codes = container.list_cache.get(db_user.user_id, context) or []
    animes = [a for a in [await container.animes.get_by_code(c) for c in codes] if a]

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context=context, page=page)
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# #29 Advanced Filter
# ---------------------------------------------------------------------------


@router.callback_query(F.data == _MENU_FILTER)
async def start_filter(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    await state.set_state(FilterStates.waiting_genre)
    await callback.message.answer(t("filter_ask_genre", db_user.language))
    await callback.answer()


@router.message(FilterStates.waiting_genre, F.text)
async def filter_genre(message: Message, state: FSMContext, db_user: User) -> None:
    if message.text.strip() != "/skip":
        await state.update_data(genre=message.text.strip())
    await state.set_state(FilterStates.waiting_year)
    await message.answer(t("filter_ask_year", db_user.language))


@router.message(FilterStates.waiting_year, F.text)
async def filter_year(message: Message, state: FSMContext, db_user: User) -> None:
    text = message.text.strip()
    if text != "/skip" and text.isdigit():
        await state.update_data(year=int(text))
    await state.set_state(FilterStates.waiting_studio)
    await message.answer(t("filter_ask_studio", db_user.language))


@router.message(FilterStates.waiting_studio, F.text)
async def filter_studio(message: Message, state: FSMContext, db_user: User) -> None:
    if message.text.strip() != "/skip":
        await state.update_data(studio=message.text.strip())
    await state.set_state(FilterStates.waiting_min_rating)
    await message.answer(t("filter_ask_rating", db_user.language))


@router.message(FilterStates.waiting_min_rating, F.text)
async def filter_min_rating(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    text = message.text.strip()
    if text != "/skip":
        try:
            await state.update_data(min_rating=float(text))
        except ValueError:
            pass

    criteria = await state.get_data()
    await state.clear()

    animes = await container.anime_service.advanced_filter(**criteria)
    if not animes:
        await message.answer(t("not_found", db_user.language))
        return

    codes = [a.code for a in animes]
    context = "advfilter"
    container.list_cache.set(db_user.user_id, context, codes)

    await message.answer(
        f"🎛 {len(animes)} ta natija:",
        reply_markup=anime_list_keyboard(animes, context=context, page=1),
    )


@router.callback_query(F.data.startswith("pg:advfilter:"))
async def paginate_filter(callback: CallbackQuery, container: Container, db_user: User) -> None:
    page = int(callback.data.split(":")[-1])
    codes = container.list_cache.get(db_user.user_id, "advfilter") or []
    animes = [a for a in [await container.animes.get_by_code(c) for c in codes] if a]

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=anime_list_keyboard(animes, context="advfilter", page=page)
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# #30 Anime Compare
# ---------------------------------------------------------------------------


@router.callback_query(F.data == _MENU_COMPARE)
async def start_compare(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    await state.set_state(CompareStates.waiting_first_code)
    await callback.message.answer(t("compare_ask_first", db_user.language))
    await callback.answer()


@router.message(CompareStates.waiting_first_code, F.text)
async def compare_first_code(message: Message, state: FSMContext, db_user: User) -> None:
    await state.update_data(code_a=message.text.strip().upper())
    await state.set_state(CompareStates.waiting_second_code)
    await message.answer(t("compare_ask_second", db_user.language))


@router.message(CompareStates.waiting_second_code, F.text)
async def compare_second_code(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    data = await state.get_data()
    code_b = message.text.strip().upper()
    await state.clear()

    anime_a, anime_b = await container.anime_service.compare(data["code_a"], code_b)
    if anime_a is None or anime_b is None:
        await message.answer(t("not_found", db_user.language))
        return

    def _row(a) -> str:
        return (
            f"<b>{a.title_uz}</b>\n"
            f"  📅 Yil: {a.year or '—'}\n"
            f"  🏷 Janr: {', '.join(a.genres) or '—'}\n"
            f"  ⭐️ Reyting: {a.average_rating}/10 ({a.rating_count} baho)\n"
            f"  👁 Ko'rishlar: {a.views}\n"
            f"  🎬 Studiya: {a.studio or '—'}"
        )

    text = f"⚖️ <b>Solishtiruv</b>\n\n{_row(anime_a)}\n\n— vs —\n\n{_row(anime_b)}"
    await message.answer(text)
