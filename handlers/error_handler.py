"""Global xato ushlagich (error handler).

Har qanday handlerda kutilmagan (unhandled) exception yuz bersa, aiogram
uni ichki ravishda faqat logga yozadi va FOYDALANUVCHIGA HECH QANDAY JAVOB
BERMAYDI — bu botning "muzlab qolgandek" ko'rinishiga olib keladi va
foydalanuvchi tajribasini yomonlashtiradi.

Bu modul shu bo'shliqni to'ldiradi:
    1. Xatoni to'liq stack-trace bilan logga yozadi (diagnostika uchun).
    2. Foydalanuvchiga tushunarli, do'stona xabar yuboradi (agar xabar/
       callback obyekti mavjud bo'lsa).
    3. Asosiy adminlarga qisqa xato haqida xabar yuboradi (production
       monitoring uchun) — spam bo'lmasligi uchun xato turi bo'yicha
       cheklangan chastota bilan.
"""

from __future__ import annotations

import time

from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, ErrorEvent, Message

from container import Container, get_container
from utils.logger import get_logger

logger = get_logger(__name__)

_GENERIC_ERROR_TEXT_UZ = "⚠️ Kutilmagan xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."

# Bir xil xato turi uchun adminlarga xabar yuborish chastotasini cheklash
# (spam bo'lmasligi uchun) — soniyalarda.
_ADMIN_ALERT_COOLDOWN_SECONDS = 300
_last_admin_alert: dict[str, float] = {}


async def _notify_user(event: ErrorEvent) -> None:
    """Foydalanuvchiga do'stona xabar yuborishga urinadi (xato ustidan
    xato chiqmasligi uchun ehtiyotkorlik bilan, jim muvaffaqiyatsizlik
    bilan)."""

    update = event.update
    try:
        if update.message is not None:
            await update.message.answer(_GENERIC_ERROR_TEXT_UZ)
        elif update.callback_query is not None:
            await update.callback_query.answer(_GENERIC_ERROR_TEXT_UZ, show_alert=True)
    except Exception as notify_exc:  # noqa: BLE001 — bu yerda xato chiqishi mumkin emas
        logger.error("Foydalanuvchiga xato haqida xabar berib bo'lmadi: %s", notify_exc)


async def _notify_admins(bot: Bot, container: Container, error_key: str, summary: str) -> None:
    """Kritik xato haqida asosiy adminlarga xabar beradi (chastota
    cheklangan holda)."""

    now = time.monotonic()
    last = _last_admin_alert.get(error_key, 0.0)
    if now - last < _ADMIN_ALERT_COOLDOWN_SECONDS:
        return
    _last_admin_alert[error_key] = now

    for admin_id in container.settings.main_admin_ids:
        try:
            await bot.send_message(admin_id, f"🚨 <b>Bot xatosi</b>\n\n<code>{summary}</code>")
        except Exception:  # noqa: BLE001
            pass


def register_error_handler(dp: Dispatcher) -> None:
    """Dispatcher'ga global xato ushlagichini ro'yxatdan o'tkazadi."""

    @dp.errors()
    async def handle_error(event: ErrorEvent, bot: Bot) -> bool:
        exc = event.exception
        update = event.update

        user_id = None
        if update.message and update.message.from_user:
            user_id = update.message.from_user.id
        elif update.callback_query and update.callback_query.from_user:
            user_id = update.callback_query.from_user.id

        logger.error(
            "Ushlanmagan xato (user=%s, update_id=%s): %s",
            user_id,
            update.update_id,
            exc,
            exc_info=True,
        )

        await _notify_user(event)

        try:
            container = get_container()
            error_key = f"{type(exc).__name__}"
            summary = f"{type(exc).__name__}: {exc}"[:500]
            await _notify_admins(bot, container, error_key, summary)
        except Exception as admin_notify_exc:  # noqa: BLE001
            logger.error("Adminlarga xato xabari yuborilmadi: %s", admin_notify_exc)

        # ``True`` qaytarish — aiogram'ga xato "ushlangani" va yana
        # yuqoriga (masalan, jarayonni to'xtatuvchi darajaga) tarqalishi
        # shart emasligini bildiradi.
        return True
