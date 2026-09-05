"""📊 Poll (#45) va 🧠 Quiz (#46) yaratish — admin."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin
from keyboards.user.poll import poll_options_keyboard

router = Router(name="admin_poll")
router.message.filter(IsAdmin())


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.POLL_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


@router.message(F.text.startswith("/createpoll "))
async def create_poll(message: Message, container: Container) -> None:
    """Format: /createpoll <savol> | <variant1> | <variant2> | ..."""

    if not await _require_permission(message, container):
        return

    body = message.text[len("/createpoll "):]
    parts = [p.strip() for p in body.split("|")]
    if len(parts) < 3:
        await message.answer(
            "⚠️ Format: /createpoll <savol> | <variant1> | <variant2> | ..."
        )
        return

    question, options = parts[0], parts[1:]
    poll = await container.poll_service.create_poll(question, options, message.from_user.id)
    await message.answer(
        f"📊 <b>{poll.question}</b>", reply_markup=poll_options_keyboard(poll.id, poll.options)
    )


@router.message(F.text.startswith("/createquiz "))
async def create_quiz(message: Message, container: Container) -> None:
    """Format: /createquiz <savol> | <variant1> | <variant2> | ... | <to'g'ri_raqam>

    <to'g'ri_raqam> — to'g'ri variantning raqami (1 dan boshlab).
    """

    if not await _require_permission(message, container):
        return

    body = message.text[len("/createquiz "):]
    parts = [p.strip() for p in body.split("|")]
    if len(parts) < 4:
        await message.answer(
            "⚠️ Format: /createquiz <savol> | <variant1> | <variant2> | ... | <to'g'ri_raqam>"
        )
        return

    question = parts[0]
    *options, correct_raw = parts[1:]
    if not correct_raw.isdigit():
        await message.answer("⚠️ Oxirgi qism to'g'ri variant RAQAMI bo'lishi kerak (1 dan boshlab).")
        return

    correct_index = int(correct_raw) - 1
    if not (0 <= correct_index < len(options)):
        await message.answer("⚠️ To'g'ri variant raqami variantlar sonidan oshib ketdi.")
        return

    q = await container.quiz_service.create_question(
        question, options, correct_index, message.from_user.id
    )
    await message.answer(f"✅ Savol qo'shildi: {q.question}")
