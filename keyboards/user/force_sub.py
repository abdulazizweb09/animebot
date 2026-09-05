"""Majburiy obuna klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.i18n import t


def force_sub_keyboard(channels: list[dict], language: str) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url = ch.get("invite_link") or f"https://t.me/{str(ch.get('username', '')).lstrip('@')}"
        rows.append([InlineKeyboardButton(text=f"📢 {ch.get('title', 'Kanal')}", url=url)])
    rows.append(
        [InlineKeyboardButton(text=t("force_sub_check_btn", language), callback_data="force_sub_check")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
