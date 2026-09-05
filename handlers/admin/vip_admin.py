"""Admin tomonidan VIP so'rovlarini tasdiqlash/rad etish."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.constants import CONSTANTS
from config.enums import Permission, VipPlan
from container import Container
from filters.admin_filters import IsAdmin
from keyboards.admin.vip_admin import vip_review_keyboard
from states.admin_states import VipReviewStates

router = Router(name="admin_vip")
router.callback_query.filter(IsAdmin())
router.message.filter(IsAdmin())


async def _require_permission(container: Container, user_id: int) -> bool:
    return await container.permission_service.has_permission(user_id, Permission.VIP_APPROVE)


@router.message(F.text == "💎 VIP so'rovlar")
async def list_pending_vip(message: Message, container: Container) -> None:
    if not await _require_permission(container, message.from_user.id):
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    pending = await container.vip_service.list_pending()
    if not pending:
        await message.answer("💎 Hozircha kutilayotgan VIP so'rovlar yo'q.")
        return

    for sub in pending:
        plan = VipPlan(sub.plan)
        caption = (
            f"💎 VIP so'rov\n\n"
            f"👤 User: <code>{sub.user_id}</code>\n"
            f"📦 Reja: {plan.label_uz}\n"
            f"💵 Narx: {sub.price:,} so'm".replace(",", " ")
        )
        if sub.receipt_file_id:
            await message.answer_photo(
                sub.receipt_file_id, caption=caption, reply_markup=vip_review_keyboard(sub.id)
            )
        else:
            await message.answer(caption, reply_markup=vip_review_keyboard(sub.id))


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_VIP}:approve:"))
async def approve_vip(callback: CallbackQuery, bot: Bot, container: Container) -> None:
    if not await _require_permission(container, callback.from_user.id):
        await callback.answer("🚫 Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return

    sub_id = callback.data.split(":", 2)[2]
    sub = await container.vip_service.approve(sub_id, callback.from_user.id)
    if sub is None:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    plan = VipPlan(sub.plan)
    awarded = await container.achievement_service.award_vip_badge(sub.user_id)
    await bot.send_message(
        sub.user_id,
        f"🎉 VIP obunangiz tasdiqlandi!\n📦 Reja: {plan.label_uz}\n"
        f"📅 Tugash sanasi: {sub.expires_at[:10]}",
    )
    if awarded:
        from config.badges import VIP_BADGE

        await bot.send_message(
            sub.user_id, f"🏆 Yangi yutuq: <b>{VIP_BADGE.label}</b>\n{VIP_BADGE.description}"
        )

    # #VIP Tier — obuna tasdiqlangandan so'ng, foydalanuvchining umrbod
    # loyallik darajasi o'zgargan-o'zgarmaganini tekshiramiz.
    tier = await container.vip_service.get_tier(sub.user_id)
    tier_badge = await container.achievement_service.award_vip_tier_badge(sub.user_id, tier)
    if tier_badge:
        await bot.send_message(
            sub.user_id,
            f"🌟 Tabriklaymiz! Siz endi <b>{tier.label}</b> darajasidasiz!\n"
            f"🏆 {tier_badge.label} — {tier_badge.description}",
        )
    if callback.message:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n✅ TASDIQLANDI"
        )
    await callback.answer("Tasdiqlandi ✅")


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_VIP}:reject:"))
async def start_reject_vip(callback: CallbackQuery, state: FSMContext, container: Container) -> None:
    if not await _require_permission(container, callback.from_user.id):
        await callback.answer("🚫 Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return

    sub_id = callback.data.split(":", 2)[2]
    await state.update_data(reject_sub_id=sub_id, reject_message_id=callback.message.message_id)
    await state.set_state(VipReviewStates.waiting_reject_reason)
    await callback.message.answer("❌ Rad etish sababini yozing:")
    await callback.answer()


@router.message(VipReviewStates.waiting_reject_reason)
async def finish_reject_vip(
    message: Message, state: FSMContext, bot: Bot, container: Container
) -> None:
    data = await state.get_data()
    sub_id = data.get("reject_sub_id")
    await state.clear()

    if not sub_id:
        await message.answer("⚠️ Xatolik yuz berdi.")
        return

    reason = message.text or "Sabab ko'rsatilmagan"
    sub = await container.vip_service.reject(sub_id, message.from_user.id, reason)
    if sub is None:
        await message.answer("So'rov topilmadi.")
        return

    await bot.send_message(
        sub.user_id, f"❌ VIP so'rovingiz rad etildi.\nSabab: {reason}"
    )
    await message.answer("Rad etildi va foydalanuvchiga xabar berildi.")
