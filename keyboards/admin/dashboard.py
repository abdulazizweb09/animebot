"""#60 Interactive Admin Dashboard — tugmali boshqaruv paneli."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def dashboard_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📊 Health", callback_data="dash:health"),
            InlineKeyboardButton(text="📈 Statistika", callback_data="dash:stats"),
        ],
        [
            InlineKeyboardButton(text="💎 VIP so'rovlar", callback_data="dash:vip"),
            InlineKeyboardButton(text="📋 Oxirgi loglar", callback_data="dash:logs"),
        ],
        [
            InlineKeyboardButton(text="🔧 JSON tuzatish", callback_data="dash:repair"),
            InlineKeyboardButton(text="🧹 Duplicate tozalash", callback_data="dash:dedup"),
        ],
        [
            InlineKeyboardButton(text="🗑 Trash optimallash", callback_data="dash:trash"),
            InlineKeyboardButton(text="💾 Backup yaratish", callback_data="dash:backup"),
        ],
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="dash:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dashboard_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Dashboard", callback_data="dash:home")]]
    )
