"""📢 Xabar yuborish (broadcast) — admin, endi maqsatli auditoriya bilan."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.enums import LogAction, Permission
from container import Container
from filters.admin_filters import IsAdmin
from keyboards.admin.confirm import confirm_keyboard
from states.admin_states import BroadcastStates

router = Router(name="admin_broadcast")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _audience_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="👥 Hammaga", callback_data="bcaud:all")],
        [InlineKeyboardButton(text="💎 Faqat VIP'larga", callback_data="bcaud:vip")],
        [InlineKeyboardButton(text="🎯 VIP bo'lmaganlarga (targ'ib)", callback_data="bcaud:nonvip")],
        [InlineKeyboardButton(text="😴 Faol bo'lmaganlarga (14+ kun)", callback_data="bcaud:inactive")],
        [InlineKeyboardButton(text="🏷 Muayyan janr sevimlilariga", callback_data="bcaud:genre")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "📢 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.BROADCAST_SEND
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return
    await state.set_state(BroadcastStates.waiting_content)
    await message.answer(
        "📢 Yubormoqchi bo'lgan xabaringizni yuboring (matn, rasm, video — istalgan turda):"
    )


@router.message(BroadcastStates.waiting_content)
async def broadcast_content_received(message: Message, state: FSMContext) -> None:
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastStates.waiting_audience)
    await message.answer("🎯 Kimlarga yuborilsin?", reply_markup=_audience_keyboard())


@router.callback_query(BroadcastStates.waiting_audience, F.data.startswith("bcaud:"))
async def audience_selected(callback: CallbackQuery, state: FSMContext, container: Container) -> None:
    audience_code = callback.data.split(":", 1)[1]

    if audience_code == "genre":
        await state.set_state(BroadcastStates.waiting_genre)
        await callback.message.answer("🏷 Janr nomini kiriting (masalan: Action):")
        await callback.answer()
        return

    labels = {
        "all": "👥 Hammaga",
        "vip": "💎 Faqat VIP'larga",
        "nonvip": "🎯 VIP bo'lmaganlarga",
        "inactive": "😴 Faol bo'lmaganlarga (14+ kun)",
    }
    await state.update_data(audience=audience_code)
    await state.set_state(BroadcastStates.confirm)
    await callback.message.answer(
        f"☝️ Ushbu xabar \"{labels.get(audience_code, audience_code)}\" auditoriyasiga yuborilsinmi?",
        reply_markup=confirm_keyboard("broadcast"),
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_genre, F.text)
async def genre_entered(message: Message, state: FSMContext) -> None:
    genre = message.text.strip()
    await state.update_data(audience="genre", genre=genre)
    await state.set_state(BroadcastStates.confirm)
    await message.answer(
        f"☝️ Ushbu xabar \"{genre}\" janri sevimlilariga yuborilsinmi?",
        reply_markup=confirm_keyboard("broadcast"),
    )


async def _resolve_audience(container: Container, data: dict) -> list[int]:
    audience = data.get("audience", "all")
    if audience == "vip":
        return await container.audience_service.vip_user_ids()
    if audience == "nonvip":
        return await container.audience_service.non_vip_user_ids()
    if audience == "inactive":
        return await container.audience_service.inactive_user_ids(days=14)
    if audience == "genre":
        return await container.audience_service.genre_fans_user_ids(data.get("genre", ""))
    return await container.users.all_active_ids()


@router.callback_query(BroadcastStates.confirm, F.data == "cnf:broadcast")
async def confirm_broadcast(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    data = await state.get_data()
    await state.clear()

    await callback.message.answer("📤 Yuborilmoqda, biroz kuting...")
    user_ids = await _resolve_audience(container, data)

    if not user_ids:
        await callback.message.answer("⚠️ Bu auditoriyada hech kim topilmadi.")
        await callback.answer()
        return

    success, failed = await container.broadcast_service.send_to_users(
        callback.message.bot,
        user_ids=user_ids,
        from_chat_id=data["chat_id"],
        message_id=data["message_id"],
        sent_by=callback.from_user.id,
    )
    await container.audit_service.log(
        callback.from_user.id,
        LogAction.BROADCAST_SEND,
        {"success": success, "failed": failed, "audience": data.get("audience", "all")},
    )
    await callback.message.answer(f"✅ Yuborildi: {success} ta\n❌ Xato: {failed} ta")
    await callback.answer()


@router.callback_query(BroadcastStates.confirm, F.data == "cxl:broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Bekor qilindi.")
    await callback.answer()
