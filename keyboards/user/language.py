"""Til tanlash klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS
from config.enums import UserLanguage


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{lang.flag} {lang.label}",
                callback_data=f"{CONSTANTS.CB_LANG}:{lang.value}",
            )
        ]
        for lang in UserLanguage
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
