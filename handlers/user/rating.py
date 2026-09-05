"""⭐️ Baholash va 💬 Izohlar — anime kartochkasi bilan bog'liq yangi
funksiyalar.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from container import Container
from database.models.user import User
from keyboards.user.anime_card import rating_score_keyboard
from states.user_states import CommentStates
from utils.i18n import t

router = Router(name="user_rating")


# ---------------------------------------------------------------------------
# Baholash
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("rate:menu:"))
async def show_rating_menu(callback: CallbackQuery, container: Container, db_user: User) -> None:
    anime_code = callback.data.split(":", 2)[2]

    stats = await container.rating_service.anime_stats(anime_code)
    existing = await container.rating_service.get_user_rating(db_user.user_id, anime_code)

    lines = [t("rate_prompt", db_user.language)]
    if stats["count"] > 0:
        lines.append(f"\n📊 Jamoa bahosi: {stats['average']}/10 ({stats['count']} ta baho)")
    if existing:
        lines.append(f"⭐️ Sizning bahoyingiz: {existing.score}/10 (o'zgartirish uchun qayta tanlang)")

    await callback.message.answer(
        "\n".join(lines), reply_markup=rating_score_keyboard(anime_code)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate:set:"))
async def set_rating(callback: CallbackQuery, container: Container, db_user: User) -> None:
    _, _, anime_code, score_raw = callback.data.split(":")
    score = int(score_raw)

    await container.rating_service.rate(db_user.user_id, anime_code, score)
    await callback.message.edit_text(t("rate_saved", db_user.language, score=score))
    await callback.answer()


# ---------------------------------------------------------------------------
# Izohlar
# ---------------------------------------------------------------------------


def _comments_footer_keyboard(anime_code: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ Izoh qoldirish", callback_data=f"addcomment:{anime_code}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _comment_actions_keyboard(comment_id: str, likes: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"comment:like:{comment_id}"),
            InlineKeyboardButton(text="🚩 Shikoyat", callback_data=f"comment:report:{comment_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("comments:"))
async def show_comments(callback: CallbackQuery, container: Container, db_user: User) -> None:
    parts = callback.data.split(":")
    anime_code = parts[1]

    comments = await container.comment_service.list_for_anime(anime_code, limit=10)
    if not comments:
        await callback.message.answer(t("comments_empty", db_user.language))
        await callback.answer()
        return

    for c in comments:
        user = await container.users.get_by_id(c.user_id)
        name = (user.full_name or user.username or "Anonim") if user else "Anonim"
        await callback.message.answer(
            f"👤 <b>{name}</b>: {c.text}",
            reply_markup=_comment_actions_keyboard(c.id, c.likes),
        )

    await callback.message.answer(
        "☝️ Izohlar", reply_markup=_comments_footer_keyboard(anime_code)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comment:like:"))
async def like_comment(callback: CallbackQuery, container: Container) -> None:
    comment_id = callback.data.split(":", 2)[2]
    comment = await container.comment_service.toggle_like(comment_id, callback.from_user.id)
    if comment is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await callback.message.edit_reply_markup(
        reply_markup=_comment_actions_keyboard(comment.id, comment.likes)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comment:report:"))
async def report_comment(callback: CallbackQuery, container: Container, db_user: User) -> None:
    comment_id = callback.data.split(":", 2)[2]
    comment = await container.comment_service.report_comment(comment_id, callback.from_user.id)
    if comment is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await callback.answer("🚩 Shikoyatingiz qabul qilindi. Moderatorlar ko'rib chiqadi.")


@router.callback_query(F.data.startswith("addcomment:"))
async def ask_comment(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    anime_code = callback.data.split(":", 1)[1]
    await state.update_data(comment_anime_code=anime_code)
    await state.set_state(CommentStates.waiting_text)
    await callback.message.answer(t("comment_ask", db_user.language))
    await callback.answer()


@router.message(CommentStates.waiting_text, F.text)
async def save_comment(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    data = await state.get_data()
    anime_code = data.get("comment_anime_code")
    await state.clear()

    if not anime_code:
        return

    await container.comment_service.add_comment(db_user.user_id, anime_code, message.text)
    await message.answer(t("comment_saved", db_user.language))
