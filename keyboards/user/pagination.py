"""Umumiy pagination qatorini yaratuvchi yordamchi funksiya."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton

from config.constants import CONSTANTS


def pagination_row(context: str, page: int, total_pages: int) -> list[InlineKeyboardButton]:
    """``context:page`` formatidagi callback_data bilan "◀️ 2/5 ▶️" qatorini quradi."""

    if total_pages <= 1:
        return []

    row: list[InlineKeyboardButton] = []
    if page > 1:
        row.append(
            InlineKeyboardButton(
                text="◀️", callback_data=f"{CONSTANTS.CB_PAGE}:{context}:{page - 1}"
            )
        )
    row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        row.append(
            InlineKeyboardButton(
                text="▶️", callback_data=f"{CONSTANTS.CB_PAGE}:{context}:{page + 1}"
            )
        )
    return row
