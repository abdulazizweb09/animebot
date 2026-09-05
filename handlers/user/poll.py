"""📊 Poll (#45) ovoz berish va 🧠 Quiz (#46) — foydalanuvchi tomoni."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from container import Container
from database.models.user import User
from keyboards.user.poll import poll_options_keyboard, quiz_options_keyboard
from utils.i18n import all_variants, t

router = Router(name="user_poll")


@router.message(F.text.in_(all_variants("btn_polls")))
async def show_active_polls(message: Message, container: Container, db_user: User) -> None:
    polls = await container.poll_service.active_polls()
    if not polls:
        await message.answer("📊 Hozircha faol so'rovlar yo'q.")
        return

    for poll in polls[:10]:
        already_voted = str(db_user.user_id) in poll.votes
        if already_voted:
            results = poll.results()
            total = sum(results) or 1
            lines = [f"📊 <b>{poll.question}</b>\n"]
            for opt, count in zip(poll.options, results):
                percent = round(count / total * 100)
                lines.append(f"  {opt}: {count} ovoz ({percent}%)")
            await message.answer("\n".join(lines))
        else:
            await message.answer(
                f"📊 <b>{poll.question}</b>",
                reply_markup=poll_options_keyboard(poll.id, poll.options),
            )


@router.callback_query(F.data.startswith("poll:vote:"))
async def vote_poll(callback: CallbackQuery, container: Container) -> None:
    _, _, poll_id, option_raw = callback.data.split(":")
    option_index = int(option_raw)

    poll = await container.poll_service.vote(poll_id, callback.from_user.id, option_index)
    if poll is None:
        await callback.answer("Xatolik.", show_alert=True)
        return

    results = poll.results()
    total = sum(results) or 1
    lines = [f"📊 <b>{poll.question}</b>\n"]
    for opt, count in zip(poll.options, results):
        percent = round(count / total * 100)
        lines.append(f"  {opt}: {count} ovoz ({percent}%)")

    if callback.message:
        await callback.message.edit_text("\n".join(lines))
    await callback.answer("✅ Ovozingiz qabul qilindi!")


@router.message(F.text.in_(all_variants("btn_quiz")))
async def start_quiz(message: Message, container: Container, db_user: User) -> None:
    question = await container.quiz_service.random_question()
    if question is None:
        await message.answer(t("quiz_empty", db_user.language))
        return

    await message.answer(
        f"🧠 {question.question}",
        reply_markup=quiz_options_keyboard(question.id, question.options),
    )


@router.callback_query(F.data.startswith("quiz:ans:"))
async def answer_quiz(callback: CallbackQuery, container: Container, db_user: User) -> None:
    _, _, question_id, chosen_raw = callback.data.split(":")
    chosen_index = int(chosen_raw)

    question = await container.quizzes.get(question_id)
    if question is None:
        await callback.answer("Xatolik.", show_alert=True)
        return

    is_correct = await container.quiz_service.answer(
        callback.from_user.id, question_id, chosen_index
    )
    await container.analytics_service.log_event(
        "quiz_answer",
        user_id=callback.from_user.id,
        meta={"question_id": question_id, "correct": is_correct},
    )

    if is_correct:
        from services.poll_service import QUIZ_CORRECT_COINS, QUIZ_CORRECT_XP

        text = t("quiz_correct", db_user.language, xp=QUIZ_CORRECT_XP, coins=QUIZ_CORRECT_COINS)
    else:
        correct_answer = question.options[question.correct_index]
        text = t("quiz_wrong", db_user.language, answer=correct_answer)

    if callback.message:
        await callback.message.edit_text(f"🧠 {question.question}\n\n{text}")
    await callback.answer()
