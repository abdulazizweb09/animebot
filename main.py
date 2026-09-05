"""Bot ishga tushirish nuqtasi.

Ishga tushirish: ``python main.py``
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import SettingsError, get_settings
from container import get_container
from database import bootstrap_json_files
from handlers import main_router
from handlers.error_handler import register_error_handler
from middlewares.container_middleware import ContainerMiddleware
from middlewares.flood_middleware import FloodMiddleware
from middlewares.throttling_middleware import ThrottlingMiddleware
from middlewares.user_middleware import UserMiddleware
from services.scheduler_service import (
    auto_backup_loop,
    schedule_watcher_loop,
    vip_watcher_loop,
    weekly_digest_loop,
)
from utils.logger import configure_logging, get_logger

logger = get_logger(__name__)

_background_tasks: list[asyncio.Task] = []


async def on_startup(bot: Bot) -> None:
    container = get_container()
    await bootstrap_json_files()

    await container.manager.update(
        "system.json",
        lambda data: {**data, "started_at": datetime.now(timezone.utc).isoformat()},
        default={"started_at": None, "version": "1.0.0", "last_health_check": None},
    )

    me = await bot.get_me()
    logger.info(
        "Bot ishga tushdi: @%s (id=%s). Asosiy adminlar: %s",
        me.username,
        me.id,
        container.settings.main_admin_ids,
    )

    _background_tasks.append(asyncio.create_task(vip_watcher_loop(bot, container)))
    _background_tasks.append(asyncio.create_task(auto_backup_loop(container)))
    _background_tasks.append(asyncio.create_task(schedule_watcher_loop(bot, container)))
    _background_tasks.append(asyncio.create_task(weekly_digest_loop(bot, container)))
    logger.info("Fon vazifalari ishga tushirildi: VIP watcher, avto-backup.")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot to'xtatilmoqda...")
    for task in _background_tasks:
        task.cancel()
    await bot.session.close()


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # MUHIM: bu middleware'lar OUTER sifatida ro'yxatdan o'tkaziladi.
    # Sabab: routerlarda IsAdmin/IsMainAdmin kabi root-filter'lar bor
    # (masalan, `router.message.filter(IsAdmin())`), va aiogram root-filter'
    # larni INNER middleware'lardan OLDIN tekshiradi. Agar bu middleware'lar
    # oddiy `.middleware()` (inner) sifatida qo'shilsa, "container" data
    # ichida hali mavjud bo'lmaydi va filter `KeyError: 'container'` bilan
    # yiqiladi. Outer middleware esa butun zanjirni — filterlarni ham,
    # handlerni ham — o'rab oladi, shuning uchun filterlar ishga tushguncha
    # "container" va "db_user" allaqachon data'da bo'ladi.
    for middleware in (
        ContainerMiddleware(),
        FloodMiddleware(),
        UserMiddleware(),
        ThrottlingMiddleware(),
    ):
        dp.message.outer_middleware(middleware)
        dp.callback_query.outer_middleware(middleware)

    dp.include_router(main_router)
    register_error_handler(dp)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    return dp


async def main() -> None:
    try:
        settings = get_settings()
    except SettingsError as exc:
        print(f"[XATO] Sozlamalarda muammo: {exc}")
        raise SystemExit(1) from exc

    configure_logging(settings.log_dir, settings.log_level)
    logger.info("Sozlamalar muvaffaqiyatli yuklandi.")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    start_time = time.monotonic()
    try:
        await dp.start_polling(bot)
    finally:
        elapsed = time.monotonic() - start_time
        logger.info("Bot %.1f soniya ishladi va to'xtadi.", elapsed)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
