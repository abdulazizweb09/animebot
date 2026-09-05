"""🎟 Promo-kod ishlatish (#16, #18)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from container import Container
from database.models.user import User
from services.promo_service import PromoRedeemError
from states.user_states import PromoStates
from utils.i18n import all_variants, t

router = Router(name="user_promo")


@router.message(F.text.in_(all_variants("btn_promo")))
async def ask_promo_code(message: Message, state: FSMContext, db_user: User) -> None:
    await state.set_state(PromoStates.waiting_code)
    await message.answer(t("promo_ask_code", db_user.language))


@router.message(PromoStates.waiting_code, F.text)
async def redeem_promo(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
    await state.clear()
    code = message.text.strip()

    try:
        promo, description = await container.promo_service.redeem(db_user.user_id, code)
    except PromoRedeemError as exc:
        await message.answer(t("promo_error", db_user.language, error=str(exc)))
        return

    await container.analytics_service.log_event(
        "promo_redeem", user_id=db_user.user_id, meta={"code": promo.code, "type": promo.type}
    )
    await message.answer(t("promo_success", db_user.language, reward=description))
