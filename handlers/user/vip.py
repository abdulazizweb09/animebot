"""💎 VIP obuna so'rash oqimi (foydalanuvchi tomoni)."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.constants import CONSTANTS
from config.enums import VipPlan
from container import Container
from database.models.user import User
from keyboards.admin.vip_admin import vip_review_keyboard
from keyboards.user.vip import vip_plans_keyboard
from states.user_states import VipStates
from utils.exceptions import VipAlreadyActiveError
from utils.i18n import all_variants
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="user_vip")


@router.message(F.text.in_(all_variants("btn_vip")))
async def show_vip_plans(message: Message, container: Container, db_user: User) -> None:
    active = await container.vip_service.get_active(db_user.user_id)
    if active:
        await message.answer(
            f"💎 Sizda faol VIP obuna bor. Tugash sanasi: {active.expires_at[:10]}"
        )
        return

    await message.answer(
        "💎 VIP rejani tanlang:", reply_markup=vip_plans_keyboard(container.settings)
    )


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_VIP}:plan:"))
async def choose_plan(callback: CallbackQuery, state: FSMContext) -> None:
    plan_value = callback.data.split(":", 2)[2]
    await state.update_data(vip_plan=plan_value)
    await state.set_state(VipStates.waiting_receipt)
    await callback.message.answer(
        "💳 To'lovni amalga oshirib, chek/skrinshotni rasm sifatida yuboring."
    )
    await callback.answer()


@router.message(VipStates.waiting_receipt, F.photo)
async def receive_receipt(
    message: Message, state: FSMContext, bot: Bot, container: Container, db_user: User
) -> None:
    data = await state.get_data()
    plan_value = data.get("vip_plan")
    await state.clear()

    if not plan_value:
        await message.answer("⚠️ Xatolik: reja tanlanmagan. Qaytadan /start bosing.")
        return

    plan = VipPlan(plan_value)
    receipt_file_id = message.photo[-1].file_id

    try:
        sub = await container.vip_service.request_plan(db_user.user_id, plan, receipt_file_id)
    except VipAlreadyActiveError:
        await message.answer("💎 Sizda allaqachon faol VIP obuna mavjud.")
        return

    await message.answer("✅ So'rovingiz qabul qilindi. Admin tasdiqlashini kuting.")
    await container.analytics_service.log_event(
        "vip_request", user_id=db_user.user_id, meta={"plan": plan.value}
    )

    caption = (
        f"💎 Yangi VIP so'rov\n\n"
        f"👤 User: <code>{db_user.user_id}</code> (@{db_user.username or '-'})\n"
        f"📦 Reja: {plan.label_uz}\n"
        f"💵 Narx: {sub.price:,} so'm".replace(",", " ")
    )
    for admin_id in container.settings.all_admin_ids:
        try:
            await bot.send_photo(
                admin_id,
                receipt_file_id,
                caption=caption,
                reply_markup=vip_review_keyboard(sub.id),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Adminga VIP so'rovi yuborilmadi (id=%s): %s", admin_id, exc)


@router.message(VipStates.waiting_receipt)
async def receipt_wrong_type(message: Message) -> None:
    await message.answer("📸 Iltimos, chekni RASM shaklida yuboring.")
