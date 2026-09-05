"""⚙️ Sozlamalar — til, bildirishnomalar, shaxsiy statistika, ma'lumot
eksporti, anime so'rash, muammo haqida xabar berish.

Bu handler avval hech qanday funksiyaga ulanmagan "⚙️ Sozlamalar"
tugmasini to'ldiradi (oldin bosilganda bot hech narsa qilmasdi).
"""

from __future__ import annotations

import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from container import Container
from database.models.user import User
from keyboards.user.language import language_keyboard
from keyboards.user.settings import settings_keyboard
from states.user_states import AnimeRequestStates, BugReportStates
from utils.i18n import all_variants, t

router = Router(name="user_settings")


@router.message(F.text.in_(all_variants("btn_settings")))
async def show_settings(message: Message, db_user: User) -> None:
    await message.answer(t("settings_title", db_user.language), reply_markup=settings_keyboard(db_user))


@router.callback_query(F.data == "settings:lang")
async def settings_change_language(callback: CallbackQuery, db_user: User) -> None:
    await callback.message.answer(t("choose_language", db_user.language), reply_markup=language_keyboard())
    await callback.answer()


@router.callback_query(F.data == "settings:notif")
async def settings_toggle_notifications(callback: CallbackQuery, container: Container, db_user: User) -> None:
    new_value = not db_user.notifications_enabled
    await container.users.update(db_user.user_id, {"notifications_enabled": new_value})
    db_user.notifications_enabled = new_value

    key = "notif_toggled_on" if new_value else "notif_toggled_off"
    await callback.answer(t(key, db_user.language))
    await callback.message.edit_reply_markup(reply_markup=settings_keyboard(db_user))


@router.callback_query(F.data == "settings:stats")
async def settings_show_stats(callback: CallbackQuery, container: Container, db_user: User) -> None:
    stats = await container.personal_stats_service.build_summary(db_user.user_id)

    vip_line = "💎 VIP" if stats["is_vip"] else "—"
    genre_line = stats["top_genre"] or "—"

    text = (
        f"{t('my_stats_title', db_user.language)}\n\n"
        f"🎬 Ko'rilgan animelar: {stats['unique_anime_watched']}\n"
        f"🎞 Ko'rilgan qismlar: {stats['total_episodes_watched']}\n"
        f"⏱ Taxminiy vaqt: {stats['estimated_hours']} soat\n"
        f"❤️ Sevimlilar: {stats['favorites_count']}\n"
        f"🏷 Sevimli janr: {genre_line}\n\n"
        f"✨ XP: {stats['xp']} (daraja {stats['level']})\n"
        f"💰 Tangalar: {stats['coins']}\n"
        f"🏆 Yutuqlar: {stats['achievements_count']}\n"
        f"🔥 Kunlik streak: {stats['login_streak']}\n"
        f"{vip_line}\n\n"
        f"▶️ Ko'rilyapti: {stats['watching_count']} | ✅ Tugallangan: {stats['completed_count']}"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "settings:myratings")
async def settings_show_my_ratings(callback: CallbackQuery, container: Container, db_user: User) -> None:
    ratings = await container.rating_service.list_for_user(db_user.user_id)
    if not ratings:
        await callback.message.answer("⭐️ Siz hali hech qanday animega baho qo'ymagansiz.")
        await callback.answer()
        return

    lines = ["⭐️ <b>Mening baholarim:</b>\n"]
    for r in ratings[:30]:
        anime = await container.animes.get_by_code(r.anime_code)
        title = anime.title_uz if anime else r.anime_code
        lines.append(f"  • {title}: {r.score}/10")

    await callback.message.answer("\n".join(lines))
    await callback.answer()
    await callback.answer()


@router.callback_query(F.data == "settings:export")
async def settings_export_data(callback: CallbackQuery, container: Container, db_user: User) -> None:
    favorites = await container.favorites.list_for_user(db_user.user_id)
    history = await container.history.list_for_user(db_user.user_id, limit=10000)
    ratings = await container.ratings.find_all(lambda r: r.get("user_id") == db_user.user_id)
    economy = await container.economy_service.get_profile(db_user.user_id)

    export = {
        "profile": db_user.to_dict(),
        "economy": economy.to_dict(),
        "favorites": [f.anime_code for f in favorites],
        "history": [{"anime_code": h.anime_code, "watched_at": h.watched_at} for h in history],
        "ratings": [{"anime_code": r.anime_code, "score": r.score} for r in ratings],
    }
    file_bytes = json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8")

    await callback.message.answer_document(
        BufferedInputFile(file_bytes, filename=f"my_data_{db_user.user_id}.json"),
        caption=t("export_ready", db_user.language),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:request")
async def settings_start_request(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    await state.set_state(AnimeRequestStates.waiting_title)
    await callback.message.answer(t("request_anime_ask", db_user.language))
    await callback.answer()


@router.message(AnimeRequestStates.waiting_title, F.text)
async def settings_save_request(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    await state.clear()
    _request, was_new = await container.anime_request_service.submit(
        db_user.user_id, message.text.strip()
    )
    if was_new:
        await message.answer(t("request_anime_saved", db_user.language))
    else:
        await message.answer(
            "👍 Bu anime allaqachon boshqa foydalanuvchi tomonidan so'ralgan — "
            "sizning ovozingiz qo'shildi!"
        )


@router.callback_query(F.data == "settings:bug")
async def settings_start_bug_report(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    await state.set_state(BugReportStates.waiting_text)
    await callback.message.answer(t("report_bug_ask", db_user.language))
    await callback.answer()


@router.message(BugReportStates.waiting_text, F.text)
async def settings_save_bug_report(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    await state.clear()
    await container.bug_report_service.submit(db_user.user_id, message.text.strip())
    await message.answer(t("report_bug_saved", db_user.language))
