"""VIP plan tanlash klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS
from config.enums import VipPlan
from config.settings import Settings


def vip_plans_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{plan.label_uz} — {settings.vip_pricing.price_for(plan):,} so'm".replace(",", " "),
                callback_data=f"{CONSTANTS.CB_VIP}:plan:{plan.value}",
            )
        ]
        for plan in VipPlan
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
