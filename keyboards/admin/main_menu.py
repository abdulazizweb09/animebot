"""Admin panel asosiy menyusi."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def admin_menu_keyboard(is_main_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🎬 Anime qo'shish"), KeyboardButton(text="📼 Video qo'shish")],
        [KeyboardButton(text="🗑 Anime o'chirish"), KeyboardButton(text="♻️ Trash")],
        [KeyboardButton(text="💎 VIP so'rovlar"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Xabar yuborish"), KeyboardButton(text="📋 Loglar")],
        [KeyboardButton(text="🔗 Majburiy obuna"), KeyboardButton(text="🚫 Ban/Unban")],
        [KeyboardButton(text="🎞 Kolleksiyalar"), KeyboardButton(text="💾 Backup")],
        [KeyboardButton(text="🎟 Promo-kodlar"), KeyboardButton(text="🎁 VIP sovg'a")],
        [KeyboardButton(text="📅 Jadval")],
        [KeyboardButton(text="🎬 Anime so'rovlari"), KeyboardButton(text="🐛 Bug-reportlar")],
    ]
    if is_main_admin:
        rows.append(
            [KeyboardButton(text="👮 Adminlar"), KeyboardButton(text="🔑 Ruxsatlar")]
        )
    rows.append([KeyboardButton(text="⬅️ Chiqish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
