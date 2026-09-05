"""Anime kartochkasi (detail) klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS
from config.enums import WatchStatus
from database.models.anime import Anime
from utils.i18n import t


def anime_card_keyboard(anime: Anime, is_favorite: bool, language: str) -> InlineKeyboardMarkup:
    fav_text = "💔 Sevimlilardan olib tashlash" if is_favorite else "❤️ Sevimlilarga qo'shish"
    rows = [
        [
            InlineKeyboardButton(
                text="🎬 Qismlar", callback_data=f"{CONSTANTS.CB_EPISODE}:list:{anime.code}:1"
            )
        ],
        [InlineKeyboardButton(text=fav_text, callback_data=f"{CONSTANTS.CB_FAV}:{anime.code}")],
        [
            InlineKeyboardButton(text="📌 Ro'yxatga qo'shish", callback_data=f"wl:menu:{anime.code}"),
            InlineKeyboardButton(text="✍️ Progress belgilash", callback_data=f"wl:setprogress:{anime.code}"),
        ],
        [
            InlineKeyboardButton(text="⭐️ Baholash", callback_data=f"rate:menu:{anime.code}"),
            InlineKeyboardButton(text="💬 Izohlar", callback_data=f"comments:{anime.code}:1"),
        ],
        [InlineKeyboardButton(text="ℹ️ Qo'shimcha", callback_data=f"extra:{anime.code}")],
        [InlineKeyboardButton(text="🎯 O'xshash animelar", callback_data=f"similar:{anime.code}")],
        [InlineKeyboardButton(text="📤 Do'stlarga ulashish", callback_data=f"share:{anime.code}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rating_score_keyboard(anime_code: str) -> InlineKeyboardMarkup:
    """1–10 baho tanlash klaviaturasi (2 qatorda, 5 tadan)."""

    row1 = [
        InlineKeyboardButton(text=str(i), callback_data=f"rate:set:{anime_code}:{i}")
        for i in range(1, 6)
    ]
    row2 = [
        InlineKeyboardButton(text=str(i), callback_data=f"rate:set:{anime_code}:{i}")
        for i in range(6, 11)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


def watch_status_keyboard(anime_code: str) -> InlineKeyboardMarkup:
    """#53 Bookmark Folder tanlash klaviaturasi."""

    rows = [
        [InlineKeyboardButton(text=status.label_uz, callback_data=f"wl:set:{anime_code}:{status.value}")]
        for status in WatchStatus
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
