"""Umumiy tasdiqlash (ha/yo'q) klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="✅ Ha", callback_data=f"{CONSTANTS.CB_CONFIRM}:{action}"
            ),
            InlineKeyboardButton(
                text="❌ Yo'q", callback_data=f"{CONSTANTS.CB_CANCEL}:{action}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
