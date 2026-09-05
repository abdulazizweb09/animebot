"""🔗 Majburiy obuna kanallarini boshqarish (admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin
from states.admin_states import SubscriptionStates

router = Router(name="admin_subscription")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(F.text == "🔗 Majburiy obuna")
async def show_channels(message: Message, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.SUBSCRIPTION_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    channels = await container.subscription_service.list_channels(only_enabled=False)
    rows = [
        [
            InlineKeyboardButton(
                text=f"❌ O'chirish: {c['title']}", callback_data=f"subrm:{c['channel_id']}"
            )
        ]
        for c in channels
    ]
    rows.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="subadd")])

    text = "🔗 Majburiy obuna kanallari:" if channels else "🔗 Hozircha kanallar yo'q."
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "subadd")
async def start_add_channel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SubscriptionStates.waiting_channel_id)
    await callback.message.answer(
        "🔗 Kanal ID sini kiriting (masalan -1001234567890).\n"
        "Eslatma: bot shu kanalda ADMIN bo'lishi shart."
    )
    await callback.answer()


@router.message(SubscriptionStates.waiting_channel_id, F.text)
async def channel_id_entered(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not (text.lstrip("-").isdigit()):
        await message.answer("⚠️ Noto'g'ri format. Qaytadan kiriting:")
        return
    await state.update_data(channel_id=int(text))
    await state.set_state(SubscriptionStates.waiting_channel_title)
    await message.answer("📝 Kanal nomini kiriting:")


@router.message(SubscriptionStates.waiting_channel_title, F.text)
async def channel_title_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(SubscriptionStates.waiting_channel_link)
    await message.answer("🔗 Kanal username (@kanal) yoki taklif havolasini kiriting:")


@router.message(SubscriptionStates.waiting_channel_link, F.text)
async def channel_link_entered(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    await state.clear()

    link_raw = message.text.strip()
    username = link_raw.lstrip("@") if link_raw.startswith("@") else None
    invite_link = link_raw if link_raw.startswith("http") else None

    await container.subscription_service.add_channel(
        channel_id=data["channel_id"],
        title=data["title"],
        username=username,
        invite_link=invite_link,
    )
    await message.answer(f"✅ Kanal qo'shildi: {data['title']}")


@router.callback_query(F.data.startswith("subrm:"))
async def remove_channel(callback: CallbackQuery, container: Container) -> None:
    channel_id = int(callback.data.split(":", 1)[1])
    removed = await container.subscription_service.remove_channel(channel_id)
    await callback.answer("✅ O'chirildi" if removed else "❌ Topilmadi", show_alert=True)
