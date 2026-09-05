"""Kolleksiyalar ro'yxati klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.collection import AnimeCollection


def collections_keyboard(collections: list[AnimeCollection]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.title, callback_data=f"coll:{c.id}")]
        for c in collections
        if not c.is_deleted
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
