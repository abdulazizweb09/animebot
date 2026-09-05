"""📅 Anime chiqish jadvalini boshqarish (admin) — #20, #21, #22 uchun asos."""

from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin
from states.admin_states import ScheduleStates

router = Router(name="admin_schedule")
router.message.filter(IsAdmin())


@router.message(F.text == "📅 Jadval")
async def start_schedule(message: Message, state: FSMContext, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.SCHEDULE_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return
    await state.set_state(ScheduleStates.waiting_anime_code)
    await message.answer("📅 Anime kodini kiriting:")


@router.message(ScheduleStates.waiting_anime_code, F.text)
async def schedule_anime_entered(message: Message, state: FSMContext, container: Container) -> None:
    code = message.text.strip().upper()
    anime = await container.animes.get_by_code(code)
    if anime is None:
        await message.answer("❌ Bunday kod topilmadi. Qaytadan kiriting:")
        return

    await state.update_data(anime_code=code)
    await state.set_state(ScheduleStates.waiting_episode_number)
    await message.answer("🔢 Qism raqamini kiriting:")


@router.message(ScheduleStates.waiting_episode_number, F.text)
async def schedule_episode_entered(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqam kiriting:")
        return
    await state.update_data(episode_number=int(message.text.strip()))
    await state.set_state(ScheduleStates.waiting_datetime)
    await message.answer(
        "🕐 Chiqish sanasi/vaqtini kiriting (UTC), format: YYYY-MM-DD HH:MM\n"
        "Masalan: 2026-08-15 18:00"
    )


@router.message(ScheduleStates.waiting_datetime, F.text)
async def schedule_datetime_entered(
    message: Message, state: FSMContext, container: Container
) -> None:
    try:
        release_at = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        await message.answer("⚠️ Format noto'g'ri. Qaytadan: YYYY-MM-DD HH:MM")
        return

    data = await state.get_data()
    await state.clear()

    entry = await container.schedule_service.create_entry(
        anime_code=data["anime_code"],
        episode_number=data["episode_number"],
        release_at=release_at,
        created_by=message.from_user.id,
    )
    await message.answer(
        f"✅ Jadvalga qo'shildi: {entry.anime_code} — {entry.episode_number}-qism\n"
        f"🕐 {release_at.strftime('%Y-%m-%d %H:%M')} UTC"
    )
