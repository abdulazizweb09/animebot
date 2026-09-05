"""Foydalanuvchi bilan bog'liq biznes-mantiq."""

from __future__ import annotations

from datetime import datetime, timezone

from config.enums import UserLanguage, UserRole
from config.settings import Settings
from database.models.user import User
from database.repositories.user_repository import UserRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    def __init__(self, users: UserRepository, settings: Settings) -> None:
        self._users = users
        self._settings = settings

    def _role_for(self, user_id: int) -> str:
        if self._settings.is_main_admin(user_id):
            return UserRole.MAIN_ADMIN.value
        if self._settings.is_admin(user_id):
            return UserRole.ADMIN.value
        return UserRole.USER.value

    async def get_or_create(
        self, user_id: int, username: str | None, full_name: str | None
    ) -> tuple[User, bool]:
        """Foydalanuvchini qaytaradi, mavjud bo'lmasa yaratadi.

        MUHIM: bu metod ``UserMiddleware`` orqali HAR BIR update uchun
        chaqiriladi — botning eng ko'p yo'l bosiladigan qismi. Yangi
        foydalanuvchi uchun ``add_if_absent()`` ishlatiladi, chunki oddiy
        "tekshir keyin qo'sh" naqshi bilan, agar bitta user'dan ikkita
        update deyarli bir vaqtda kelsa (masalan, Telegram'ning takroriy
        update yuborishi yoki tez-tez tugma bosish), ikkalasi ham
        foydalanuvchi "mavjud emas" deb topib, BIR XIL ``user_id`` bilan
        ikkita alohida yozuv yaratib qo'yishi mumkin edi.

        Qaytaradi: ``(user, created_bo'ldimi)``
        """

        existing = await self._users.get_by_id(user_id)
        if existing is not None:
            existing.username = username
            existing.full_name = full_name
            existing.touch()
            await self._users.replace(existing)
            return existing, False

        user = User(
            user_id=user_id,
            username=username,
            full_name=full_name,
            language=UserLanguage.default().value,
            role=self._role_for(user_id),
        )
        saved, added = await self._users.add_if_absent(user)
        if added:
            logger.info("Yangi foydalanuvchi: id=%s username=%s", user_id, username)
            return saved, True

        # Bu yerga tushdi degani — parallel so'rov bizdan oldinroq shu
        # user_id bilan yozuv yaratib ulgurgan. Endi uni normal holatda
        # o'qib, yangilab qaytaramiz (duplicate yaratilmaydi).
        existing = await self._users.get_by_id(user_id)
        if existing is not None:
            existing.username = username
            existing.full_name = full_name
            existing.touch()
            await self._users.replace(existing)
            return existing, False

        # Amalda deyarli bo'lmaydigan holat (yozuv orada o'chirilgan bo'lsa) —
        # xavfsizlik uchun oxirgi chora sifatida shunchaki qaytaramiz.
        return user, False

    async def set_language(self, user_id: int, language: str) -> User | None:
        return await self._users.set_language(user_id, language)

    async def get_profile(self, user_id: int) -> User | None:
        return await self._users.get_by_id(user_id)

    async def is_banned(self, user_id: int) -> tuple[bool, str | None]:
        user = await self._users.get_by_id(user_id)
        if user is None:
            return False, None
        return user.is_banned, user.ban_reason
