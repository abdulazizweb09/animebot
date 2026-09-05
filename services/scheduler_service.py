"""Fon vazifalari (background jobs): VIP muddati tekshiruvi va avto-backup.

``asyncio.create_task`` orqali botning umumiy event loop'ida ishlaydi —
alohida process yoki cron shart emas.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from config.constants import CONSTANTS
from container import Container
from utils.logger import get_logger

logger = get_logger(__name__)

_VIP_CHECK_INTERVAL_SECONDS = 3600  # har soatda


async def _notify_expiring_vips(bot: Bot, container: Container) -> None:
    for days in CONSTANTS.VIP_EXPIRY_WARNING_DAYS:
        expiring = await container.vips.list_expiring_within(days)
        for sub in expiring:
            if days in sub.warned_days:
                continue
            try:
                await bot.send_message(
                    sub.user_id,
                    f"⏰ VIP obunangiz {days} kundan so'ng tugaydi "
                    f"({sub.expires_at[:10]}). Uzaytirish uchun 💎 VIP bo'limiga kiring.",
                )
            except TelegramForbiddenError:
                pass
            await container.vips.update(
                sub.id, {"warned_days": list(set(sub.warned_days + [days]))}
            )


async def _mark_and_notify_expired(bot: Bot, container: Container) -> None:
    expired = await container.vip_service.mark_expired()
    for sub in expired:
        try:
            await bot.send_message(
                sub.user_id, "💔 VIP obunangiz muddati tugadi. Yangilash uchun 💎 VIP bo'limiga kiring."
            )
        except TelegramForbiddenError:
            pass


async def vip_watcher_loop(bot: Bot, container: Container) -> None:
    while True:
        try:
            await _notify_expiring_vips(bot, container)
            await _mark_and_notify_expired(bot, container)
        except Exception as exc:  # noqa: BLE001 — fon vazifasi hech qachon o'lmasligi kerak
            logger.error("VIP watcher xatosi: %s", exc)
        await asyncio.sleep(_VIP_CHECK_INTERVAL_SECONDS)


async def auto_backup_loop(container: Container) -> None:
    interval = CONSTANTS.BACKUP_AUTO_INTERVAL_HOURS * 3600
    while True:
        await asyncio.sleep(interval)
        try:
            await container.backup_service.create_full_backup()
        except Exception as exc:  # noqa: BLE001
            logger.error("Avto-backup xatosi: %s", exc)


_SCHEDULE_CHECK_INTERVAL_SECONDS = 300  # har 5 daqiqada


async def _notify_users_about_release(
    bot: Bot, container: Container, anime_code: str, episode_number: int, window: str
) -> None:
    """Berilgan anime'ni sevimli/watchlist qilgan userlarga eslatma yuboradi
    (#21 Schedule Notification).
    """

    anime = await container.animes.get_by_code(anime_code)
    title = anime.title_uz if anime else anime_code

    window_label = {"1day": "1 kun", "1hour": "1 soat", "30min": "30 daqiqa"}[window]

    favorites = await container.favorites.find_all(lambda f: f.get("anime_code") == anime_code)
    watchers = await container.watchlist.find_all(lambda w: w.get("anime_code") == anime_code)
    user_ids = {f.user_id for f in favorites if not f.is_deleted} | {
        w.user_id for w in watchers if not w.is_deleted
    }

    for user_id in user_ids:
        try:
            await bot.send_message(
                user_id,
                f"⏰ <b>{title}</b> — {episode_number}-qism {window_label}dan so'ng chiqadi!",
            )
        except TelegramForbiddenError:
            pass


async def _check_schedule_notifications(bot: Bot, container: Container) -> None:
    for window in ("1day", "1hour", "30min"):
        due_entries = await container.schedule.due_for_notification(window)
        for entry in due_entries:
            await _notify_users_about_release(
                bot, container, entry.anime_code, entry.episode_number, window
            )
            await container.schedule.mark_notified(entry.id, window)

    await container.schedule.mark_released_if_due()


async def schedule_watcher_loop(bot: Bot, container: Container) -> None:
    """#21 Schedule Notification — chiqishdan 1 kun/1soat/30daqiqa oldin
    eslatma yuboradigan fon vazifasi.
    """

    while True:
        try:
            await _check_schedule_notifications(bot, container)
        except Exception as exc:  # noqa: BLE001
            logger.error("Schedule watcher xatosi: %s", exc)
        await asyncio.sleep(_SCHEDULE_CHECK_INTERVAL_SECONDS)


_WEEKLY_DIGEST_INTERVAL_SECONDS = 7 * 24 * 3600  # bir haftada bir marta


async def _build_and_send_digest(bot: Bot, container: Container, user_id: int) -> None:
    """Foydalanuvchining sevimli janrlari bo'yicha so'nggi 7 kunda
    qo'shilgan animelardan mos kelganlarini tanlab yuboradi.
    """

    favorites = await container.favorites.list_for_user(user_id)
    if not favorites:
        return  # sevimlisi yo'q — shaxsiylashtirilgan digest tuzib bo'lmaydi

    favorite_genres: set[str] = set()
    for fav in favorites:
        anime = await container.animes.get_by_code(fav.anime_code)
        if anime:
            favorite_genres.update(anime.genres)

    if not favorite_genres:
        return

    recent = await container.anime_service.recently_added(limit=30)
    matches = [a for a in recent if favorite_genres & set(a.genres)]
    if not matches:
        return

    lines = ["📬 <b>Haftalik tavsiyalar</b>\n\nSizning sevimli janrlaringizda yangi animelar:"]
    for a in matches[:5]:
        lines.append(f"  🎬 {a.title_uz} ({', '.join(a.genres)})")

    await container.notification_service.create_and_send(
        bot,
        user_id,
        kind="weekly_digest",
        title="📬 Haftalik tavsiyalar",
        text="\n".join(lines[1:]),
    )


async def weekly_digest_loop(bot: Bot, container: Container) -> None:
    """Har hafta, sevimli janrlarga mos yangi animelar haqida
    shaxsiylashtirilgan xabarnoma yuboradi."""

    # Bot ishga tushgandan darhol emas, birinchi haftadan keyin boshlanadi
    await asyncio.sleep(_WEEKLY_DIGEST_INTERVAL_SECONDS)
    while True:
        try:
            active_ids = await container.users.all_active_ids()
            for user_id in active_ids:
                try:
                    await _build_and_send_digest(bot, container, user_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Digest yuborilmadi (user=%s): %s", user_id, exc)
                await asyncio.sleep(0.05)  # flood-limitga tegmaslik uchun
        except Exception as exc:  # noqa: BLE001
            logger.error("Weekly digest loop xatosi: %s", exc)
        await asyncio.sleep(_WEEKLY_DIGEST_INTERVAL_SECONDS)
