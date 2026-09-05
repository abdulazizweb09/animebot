"""Loyihaga xos exception'lar ierarxiyasi.

Umumiy ``Exception`` yoki ``ValueError`` o'rniga shu klasslardan foydalanish
xatolarni aniq ushlash va foydalanuvchiga tushunarli xabar berishga yordam
beradi.
"""

from __future__ import annotations


class BotBaseError(Exception):
    """Botdagi barcha custom exception'larning ota klassi."""


# ---------------------------------------------------------------------------
# JSON / Storage
# ---------------------------------------------------------------------------


class StorageError(BotBaseError):
    """JSON fayl bilan ishlashda umumiy xato."""


class JsonCorruptedError(StorageError):
    """JSON fayl buzilgan (parse qilib bo'lmayapti)."""


class JsonNotFoundError(StorageError):
    """So'ralgan JSON fayli topilmadi."""


class JsonLockTimeoutError(StorageError):
    """Fayl lock'ini olishda timeout bo'ldi (boshqa jarayon band qilgan)."""


class JsonValidationError(StorageError):
    """JSON tarkibi kutilgan sxemaga mos kelmadi."""


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------


class DomainError(BotBaseError):
    """Biznes-mantiq qatlamidagi xatolar uchun ota klass."""


class UserNotFoundError(DomainError):
    pass


class AnimeNotFoundError(DomainError):
    pass


class EpisodeNotFoundError(DomainError):
    pass


class VideoNotFoundError(DomainError):
    pass


class DuplicateAnimeCodeError(DomainError):
    pass


class DuplicateFileIdError(DomainError):
    pass


class VipPlanNotFoundError(DomainError):
    pass


class VipAlreadyActiveError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class InvalidStateTransitionError(DomainError):
    pass


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------


class AIServiceError(BotBaseError):
    """Gemini API bilan ishlashda xato."""


class AIQuotaExceededError(AIServiceError):
    pass


class AIResponseEmptyError(AIServiceError):
    pass


# ---------------------------------------------------------------------------
# Rate limit / security
# ---------------------------------------------------------------------------


class RateLimitExceededError(BotBaseError):
    pass


class FloodDetectedError(BotBaseError):
    pass
