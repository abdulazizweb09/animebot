"""🚫 Foydalanuvchini ban/unban qilish (admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.enums import LogAction, Permission
from container import Container
from filters.admin_filters import IsAdmin
from states.admin_states import BanStates

router = Router(name="admin_ban")
router.message.filter(IsAdmin())


@router.message(F.text == "🚫 Ban/Unban")
async def start_ban(message: Message, state: FSMContext, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.USER_BAN
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    await state.set_state(BanStates.waiting_user_id)
    await message.answer(
        "🚫 Ban/Unban qilmoqchi bo'lgan foydalanuvchi ID sini kiriting:"
    )


@router.message(BanStates.waiting_user_id, F.text)
async def ban_user_id_entered(message: Message, state: FSMContext, container: Container) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Faqat raqamli ID kiriting:")
        return

    user_id = int(message.text.strip())
    user = await container.users.get_by_id(user_id)
    if user is None:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        await state.clear()
        return

    # Xavfsizlik: adminlar bir-birini (yoki o'zini) bloklay olmasin —
    # aks holda nizoli admin boshqa adminlarni yoki hatto o'zini
    # bloklab, botni boshqarib bo'lmaydigan holatga keltirishi mumkin.
    if container.settings.is_admin(user_id) or await container.admins.is_admin(user_id):
        await message.answer("🚫 Adminlarni ban qilib bo'lmaydi.")
        await state.clear()
        return

    if user.is_banned:
        await container.users.unban(user_id)
        await container.audit_service.log(message.from_user.id, LogAction.USER_UNBAN, {"target": user_id})
        await message.answer(f"✅ {user_id} unban qilindi.")
        await state.clear()
        return

    await state.update_data(ban_user_id=user_id)
    await state.set_state(BanStates.waiting_reason)
    await message.answer("✍️ Ban sababini kiriting:")


@router.message(BanStates.waiting_reason, F.text)
async def ban_reason_entered(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    user_id = data.get("ban_user_id")
    await state.clear()

    await container.users.ban(user_id, message.text.strip())
    await container.audit_service.log(
        message.from_user.id, LogAction.USER_BAN, {"target": user_id, "reason": message.text.strip()}
    )
    await message.answer(f"🚫 {user_id} bloklandi.")
