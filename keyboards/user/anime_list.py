"""Anime ro'yxatini (qidiruv/kategoriya natijalari) tugmalar shaklida chiqaradi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS
from database.models.anime import Anime
from keyboards.user.pagination import pagination_row


def anime_list_keyboard(
    animes: list[Anime], context: str, page: int, per_page: int = CONSTANTS.ANIME_PER_PAGE
) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(animes) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_items = animes[start : start + per_page]

    rows = [
        [
            InlineKeyboardButton(
                text=f"{a.title_uz} ({a.year or '—'})",
                callback_data=f"{CONSTANTS.CB_ANIME}:{a.code}",
            )
        ]
        for a in page_items
    ]

    nav = pagination_row(context, page, total_pages)
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)
