"""Barcha foydalanuvchilarga xabar yuborish (broadcast) logikasi."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from config.constants import CONSTANTS
from database.json_manager import JsonManager
from database.repositories.user_repository import UserRepository
from utils.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRY_ATTEMPTS = 3
_ADAPTIVE_DELAY_MULTIPLIER = 1.5
_ADAPTIVE_DELAY_MAX = 2.0
_ADAPTIVE_DELAY_DECAY = 0.95


class BroadcastService:
    def __init__(self, manager: JsonManager, users: UserRepository) -> None:
        self._manager = manager
        self._users = users

    async def _send_one(
        self, bot: Bot, user_id: int, from_chat_id: int, message_id: int
    ) -> tuple[bool, float]:
        """Bitta foydalanuvchiga xabar yuboradi, 429 (RetryAfter) kelsa
        Telegram ko'rsatgan aniq vaqtni kutib, bir necha marta qayta
        urinadi (avval faqat bitta qayta urinish bo'lib, ikkinchi marta
        ham limitga tushsa xabar butunlay yo'qolib qolardi — endi
        ``_MAX_RETRY_ATTEMPTS`` marta urinadi).

        Qaytaradi: ``(muvaffaqiyatlimi, keyingi so'rov uchun tavsiya
        etilgan qo'shimcha kutish vaqti)``.
        """

        extra_delay = 0.0
        for attempt in range(1, _MAX_RETRY_ATTEMPTS + 1):
            try:
                await bot.copy_message(
                    chat_id=user_id, from_chat_id=from_chat_id, message_id=message_id
                )
                return True, extra_delay
            except TelegramRetryAfter as exc:
                logger.warning(
                    "Broadcast rate-limit (urinish %d/%d, user=%s): %s soniya kutish",
                    attempt,
                    _MAX_RETRY_ATTEMPTS,
                    user_id,
                    exc.retry_after,
                )
                # Telegram aniq ko'rsatgan vaqtni to'liq kutamiz — bu 429
                # xatosining oldini olishning yagona ishonchli yo'li.
                await asyncio.sleep(exc.retry_after)
                extra_delay = min(
                    _ADAPTIVE_DELAY_MAX,
                    max(extra_delay, CONSTANTS.BROADCAST_DELAY_SECONDS)
                    * _ADAPTIVE_DELAY_MULTIPLIER,
                )
            except TelegramForbiddenError:
                return False, extra_delay
            except Exception as exc:  # noqa: BLE001
                logger.warning("Broadcast xato (user=%s): %s", user_id, exc)
                return False, extra_delay

        return False, extra_delay

    async def send_to_users(
        self, bot: Bot, user_ids: list[int], from_chat_id: int, message_id: int, sent_by: int
    ) -> tuple[int, int]:
        """Berilgan xabarni FAQAT ko'rsatilgan ``user_ids`` ro'yxatiga
        yuboradi — maqsadli (targeted) broadcast uchun (masalan, faqat
        VIP foydalanuvchilar yoki muayyan janr sevimlilariga).

        ``send_to_all`` ham shu metoddan foydalanadi (barcha aktiv
        userlar ro'yxati bilan chaqiradi) — kod takrorlanmasligi uchun.
        """

        success = 0
        failed = 0
        current_delay = CONSTANTS.BROADCAST_DELAY_SECONDS

        for i in range(0, len(user_ids), CONSTANTS.BROADCAST_BATCH_SIZE):
            batch = user_ids[i : i + CONSTANTS.BROADCAST_BATCH_SIZE]
            for user_id in batch:
                ok, extra_delay = await self._send_one(bot, user_id, from_chat_id, message_id)
                if ok:
                    success += 1
                else:
                    failed += 1

                if extra_delay > current_delay:
                    current_delay = extra_delay
                else:
                    current_delay = max(
                        CONSTANTS.BROADCAST_DELAY_SECONDS,
                        current_delay * _ADAPTIVE_DELAY_DECAY,
                    )

                await asyncio.sleep(current_delay)

        def _updater(data: list[dict]) -> list[dict]:
            data.append(
                {
                    "id": str(uuid.uuid4()),
                    "sent_by": sent_by,
                    "success": success,
                    "failed": failed,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return data

        await self._manager.update("broadcasts.json", _updater, default=[])
        return success, failed

    async def send_to_all(
        self, bot: Bot, from_chat_id: int, message_id: int, sent_by: int
    ) -> tuple[int, int]:
        """Berilgan xabarni (copy_message orqali) barcha aktiv userlarga yuboradi.

        Adaptiv kechikish: agar Telegram 429 (Too Many Requests) qaytarsa,
        keyingi xabarlar orasidagi kutish vaqti vaqtincha oshiriladi, so'ng
        muvaffaqiyatli yuborishlar davomida asta-sekin standart qiymatga
        qaytadi. Bu katta (100 000+) foydalanuvchi bazasida barqaror
        ishlashni ta'minlaydi.

        Qaytaradi: ``(muvaffaqiyatli, muvaffaqiyatsiz)``
        """

        user_ids = await self._users.all_active_ids()
        return await self.send_to_users(bot, user_ids, from_chat_id, message_id, sent_by)
