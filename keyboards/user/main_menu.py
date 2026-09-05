"""Asosiy menyu (reply keyboard) — soddalashtirilgan, 5 tugmali tuzilma.

Avval bu klaviaturada 15+ tugma bor edi (har bir funksiya uchun alohida),
bu esa yangi foydalanuvchini chalkashtirib yuborardi. Endi funksiyalar
mantiqiy guruhlarga (hub'larga) yig'ildi:

    🔍 Anime izlash — qidirish, kategoriya, tavsiya, tasodifiy va h.k.
    💎 VIP          — obuna sotib olish
    📖 Qo'llanma    — botdan qanday foydalanish
    🤖 AI Yordamchi — AI chat (faqat VIP)
    👤 Profil       — profil, sevimlilar, ro'yxatlar, tanga do'koni va h.k.

Barcha eski funksiyalar YO'QOLGANI YO'Q — ular shu 5 ta tugma ichidagi
inline menyular orqali hamon to'liq ishlaydi (handlers/user/search_hub.py
va handlers/user/profile_hub.py ga qarang).
"""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from utils.i18n import t


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text=t("btn_anime_search_hub", language)),
            KeyboardButton(text=t("btn_vip", language)),
        ],
        [
            KeyboardButton(text=t("btn_guide", language)),
            KeyboardButton(text=t("btn_ai", language)),
        ],
        [KeyboardButton(text=t("btn_profile_hub", language))],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
