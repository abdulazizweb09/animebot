"""AI Yordamchi — suhbat tarixini boshqarish va Gemini bilan bog'lash."""

from __future__ import annotations

from datetime import datetime, timezone

from ai.gemini_client import GeminiClient
from ai.prompts import build_system_prompt
from config.constants import CONSTANTS
from database.json_manager import JsonManager
from database.repositories.anime_repository import AnimeRepository
from database.repositories.user_repository import UserRepository
from utils.exceptions import AIServiceError, RateLimitExceededError
from utils.logger import get_logger

logger = get_logger(__name__)

# Bitta xabar matnining maksimal uzunligi (belgi). Bu Gemini'ning context
# window/token limitidan (400 Bad Request) himoyalanish uchun ikkinchi
# qatlam — xabarlar SONI CONSTANTS.AI_MAX_HISTORY_MESSAGES bilan
# cheklangan, lekin agar foydalanuvchi juda uzun matn yuborsa yoki AI juda
# uzun javob qaytarsa, bitta xabarning o'zi ham katta bo'lib qolishi mumkin.
_MAX_MESSAGE_CHARS = 4000


class AIService:
    def __init__(
        self,
        manager: JsonManager,
        client: GeminiClient,
        animes: AnimeRepository,
        users: UserRepository,
        daily_limit: int = 30,
    ) -> None:
        self._manager = manager
        self._client = client
        self._animes = animes
        self._users = users
        self._daily_limit = daily_limit

    async def _get_history(self, user_id: int) -> list[dict[str, str]]:
        all_histories = await self._manager.read("ai_history.json", default=[])
        for entry in all_histories:
            if entry.get("user_id") == user_id:
                return entry.get("messages", [])
        return []

    async def _save_history(self, user_id: int, messages: list[dict[str, str]]) -> None:
        # Ikki qatlamli himoya Gemini context/token limitidan (400 Bad
        # Request) oshib ketmaslik uchun: (1) xabarlar soni cheklanadi,
        # (2) har bir xabar matni ham cheklanadi.
        trimmed = messages[-CONSTANTS.AI_MAX_HISTORY_MESSAGES :]
        trimmed = [
            {**m, "text": m["text"][:_MAX_MESSAGE_CHARS]} for m in trimmed
        ]

        def _updater(data: list[dict]) -> list[dict]:
            for entry in data:
                if entry.get("user_id") == user_id:
                    entry["messages"] = trimmed
                    return data
            data.append({"user_id": user_id, "messages": trimmed})
            return data

        await self._manager.update("ai_history.json", _updater, default=[])

    async def _check_and_increment_rate_limit(self, user_id: int) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None:
            return

        today = datetime.now(timezone.utc).date().isoformat()
        reset_day = (user.ai_requests_reset_at or "")[:10]

        if reset_day != today:
            await self._users.update(
                user_id, {"ai_requests_today": 1, "ai_requests_reset_at": today}
            )
            return

        if user.ai_requests_today >= self._daily_limit:
            raise RateLimitExceededError(
                f"Foydalanuvchi {user_id} kunlik AI so'rov limitiga yetdi."
            )

        await self._users.update(user_id, {"ai_requests_today": user.ai_requests_today + 1})

    async def ask(self, user_id: int, message: str) -> str:
        await self._check_and_increment_rate_limit(user_id)

        history = await self._get_history(user_id)
        available_animes = await self._animes.all()
        system_prompt = build_system_prompt(available_animes[: CONSTANTS.AI_CONTEXT_ANIME_LIMIT])

        try:
            reply = await self._client.generate_reply(system_prompt, history, message)
        except AIServiceError as exc:
            # Gemini "400 Bad Request" (context/token limitidan oshib ketish)
            # yoki shunga o'xshash xato bersa — tarixni butunlay tozalab,
            # BITTA marta qaytadan urinib ko'ramiz (foydalanuvchi hech narsa
            # sezmasdan javob oladi, faqat eski kontekst yo'qoladi).
            logger.warning(
                "AI so'rovi tarixi bilan muvaffaqiyatsiz (user=%s), tarixsiz qayta urinilmoqda: %s",
                user_id,
                exc,
            )
            history = []
            reply = await self._client.generate_reply(system_prompt, history, message)

        history.append({"role": "user", "text": message})
        history.append({"role": "model", "text": reply})
        await self._save_history(user_id, history)

        return reply

    async def clear_history(self, user_id: int) -> None:
        await self._save_history(user_id, [])

    async def transcribe_voice_search(self, audio_bytes: bytes, mime_type: str) -> str:
        """#23 Voice Search — ovozli xabardan qidiruv so'zini oladi."""

        return await self._client.transcribe_audio(audio_bytes, mime_type)

    async def identify_anime_from_image(self, image_bytes: bytes, mime_type: str) -> str:
        """#24 Image Search — poster rasmidan anime nomini taxmin qiladi."""

        return await self._client.identify_anime_from_image(image_bytes, mime_type)
