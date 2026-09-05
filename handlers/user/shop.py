"""🛍 Tanga Do'koni — economy tizimidagi "chiqim" (sink) qismi.

Bu handler qo'shilishidan oldin tangalar faqat to'planardi (epizod
ko'rish, kunlik bonus, referral, viktorina), lekin ularni sarflashning
UMUMAN ILOJI YO'Q edi — bu economy tizimining eng katta bo'shlig'i edi.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.shop_items import SHOP_ITEMS, get_shop_item
from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_shop")


def _shop_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{item.label} — {item.price_coins} 💰",
                callback_data=f"shop:buy:{item.code}",
            )
        ]
        for item in SHOP_ITEMS.values()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(all_variants("btn_shop")))
async def show_shop(message: Message, container: Container, db_user: User) -> None:
    profile = await container.economy_service.get_profile(db_user.user_id)
    text = (
        f"{t('shop_title', db_user.language)}\n\n"
        f"{t('shop_your_balance', db_user.language, coins=profile.coins)}"
    )
    await message.answer(text, reply_markup=_shop_keyboard())


@router.callback_query(F.data.startswith("shop:buy:"))
async def buy_shop_item(callback: CallbackQuery, container: Container, db_user: User) -> None:
    item_code = callback.data.split(":", 2)[2]
    item = get_shop_item(item_code)
    if item is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    success = await container.economy_service.spend_coins(db_user.user_id, item.price_coins)
    if not success:
        profile = await container.economy_service.get_profile(db_user.user_id)
        await callback.answer(
            t(
                "shop_insufficient_funds",
                db_user.language,
                price=item.price_coins,
                coins=profile.coins,
            ),
            show_alert=True,
        )
        return

    if item.kind == "vip_days":
        await container.promo_service.gift_vip(callback.from_user.id, db_user.user_id, item.value)

    await container.analytics_service.log_event(
        "shop_purchase", user_id=db_user.user_id, meta={"item": item.code, "price": item.price_coins}
    )
    await callback.answer(
        t("shop_buy_success", db_user.language, item=item.label), show_alert=True
    )
