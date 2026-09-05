"""Video yuklashda sifat tanlash klaviaturasi (admin)."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

QUALITIES = ["480p", "720p", "1080p"]


def quality_select_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=q, callback_data=f"upl_q:{q}")] for q in QUALITIES
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
