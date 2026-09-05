"""Admin uchun VIP so'rovini tasdiqlash/rad etish klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS


def vip_review_keyboard(sub_id: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash", callback_data=f"{CONSTANTS.CB_VIP}:approve:{sub_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish", callback_data=f"{CONSTANTS.CB_VIP}:reject:{sub_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
