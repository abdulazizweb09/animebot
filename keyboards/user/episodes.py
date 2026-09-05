"""Epizodlar ro'yxati va video sifat tanlash klaviaturalari."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS
from database.models.anime import Episode, Video
from keyboards.user.pagination import pagination_row

EPISODES_PER_PAGE = 10


def episode_list_keyboard(
    anime_code: str, episodes: list[Episode], page: int = 1
) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(episodes) + EPISODES_PER_PAGE - 1) // EPISODES_PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * EPISODES_PER_PAGE
    page_items = episodes[start : start + EPISODES_PER_PAGE]

    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for ep in page_items:
        row.append(
            InlineKeyboardButton(
                text=str(ep.number),
                callback_data=f"{CONSTANTS.CB_EPISODE}:open:{ep.id}",
            )
        )
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav = pagination_row(f"eps:{anime_code}", page, total_pages)
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def video_quality_keyboard(episode_id: str, videos: list[Video]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"▶️ {v.quality}",
                callback_data=f"{CONSTANTS.CB_VIDEO}:{episode_id}:{v.quality}",
            )
        ]
        for v in videos
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
