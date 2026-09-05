"""⚙️ Sozlamalar menyusi klaviaturasi."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.user import User
from utils.i18n import t


def settings_keyboard(db_user: User) -> InlineKeyboardMarkup:
    notif_text = (
        t("settings_notifications_on", db_user.language)
        if db_user.notifications_enabled
        else t("settings_notifications_off", db_user.language)
    )
    rows = [
        [InlineKeyboardButton(text=t("settings_language", db_user.language), callback_data="settings:lang")],
        [InlineKeyboardButton(text=notif_text, callback_data="settings:notif")],
        [InlineKeyboardButton(text=t("settings_my_stats", db_user.language), callback_data="settings:stats")],
        [InlineKeyboardButton(text="⭐️ Mening baholarim", callback_data="settings:myratings")],
        [InlineKeyboardButton(text=t("settings_export_data", db_user.language), callback_data="settings:export")],
        [InlineKeyboardButton(text=t("settings_request_anime", db_user.language), callback_data="settings:request")],
        [InlineKeyboardButton(text=t("settings_report_bug", db_user.language), callback_data="settings:bug")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
