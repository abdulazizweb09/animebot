"""Butun loyihada ishlatiladigan enum'lar.

Magic string/number ishlatmaslik uchun barcha doimiy qiymatlar shu yerda
belgilanadi.
"""

from __future__ import annotations

from enum import Enum


class UserLanguage(str, Enum):
    """Foydalanuvchi tili."""

    UZBEK = "uz"
    RUSSIAN = "ru"
    ENGLISH = "en"

    @classmethod
    def default(cls) -> "UserLanguage":
        return cls.UZBEK

    @property
    def flag(self) -> str:
        return {
            UserLanguage.UZBEK: "🇺🇿",
            UserLanguage.RUSSIAN: "🇷🇺",
            UserLanguage.ENGLISH: "🇺🇸",
        }[self]

    @property
    def label(self) -> str:
        return {
            UserLanguage.UZBEK: "O'zbek",
            UserLanguage.RUSSIAN: "Русский",
            UserLanguage.ENGLISH: "English",
        }[self]


class UserRole(str, Enum):
    """Foydalanuvchi roli."""

    USER = "user"
    ADMIN = "admin"
    MAIN_ADMIN = "main_admin"


class VipPlan(str, Enum):
    """VIP obuna muddati."""

    ONE_MONTH = "1_month"
    THREE_MONTHS = "3_months"
    SIX_MONTHS = "6_months"
    TWELVE_MONTHS = "12_months"

    @property
    def days(self) -> int:
        return {
            VipPlan.ONE_MONTH: 30,
            VipPlan.THREE_MONTHS: 90,
            VipPlan.SIX_MONTHS: 180,
            VipPlan.TWELVE_MONTHS: 365,
        }[self]

    @property
    def label_uz(self) -> str:
        return {
            VipPlan.ONE_MONTH: "1 oy",
            VipPlan.THREE_MONTHS: "3 oy",
            VipPlan.SIX_MONTHS: "6 oy",
            VipPlan.TWELVE_MONTHS: "12 oy",
        }[self]


class VipTier(str, Enum):
    """VIP loyallik darajasi — umrbod olingan VIP kunlar yig'indisiga
    asoslanadi (rejadan farqli, bu qayta tiklanmaydi, doim o'sib boradi).
    """

    NONE = "none"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"

    @property
    def label(self) -> str:
        return {
            VipTier.NONE: "—",
            VipTier.BRONZE: "🥉 Bronze VIP",
            VipTier.SILVER: "🥈 Silver VIP",
            VipTier.GOLD: "🥇 Gold VIP",
        }[self]

    @property
    def daily_bonus_multiplier(self) -> float:
        """Kunlik bonusga (Daily Reward) qo'shimcha ko'paytiruvchi."""

        return {
            VipTier.NONE: 1.0,
            VipTier.BRONZE: 1.1,
            VipTier.SILVER: 1.25,
            VipTier.GOLD: 1.5,
        }[self]

    @classmethod
    def for_cumulative_days(cls, days: int) -> "VipTier":
        if days >= 365:
            return cls.GOLD
        if days >= 90:
            return cls.SILVER
        if days >= 1:
            return cls.BRONZE
        return cls.NONE


class VipStatus(str, Enum):
    """VIP so'rovi / obuna holati."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AnimeStatus(str, Enum):
    """Anime chiqish holati."""

    ONGOING = "ongoing"
    COMPLETED = "completed"
    ANNOUNCED = "announced"
    PAUSED = "paused"


class AnimeType(str, Enum):
    """Anime turi: TV serial / Film / OVA / Maxsus qism (#37-39)."""

    TV = "tv"
    MOVIE = "movie"
    OVA = "ova"
    SPECIAL = "special"

    @property
    def label_uz(self) -> str:
        return {
            AnimeType.TV: "📺 TV Serial",
            AnimeType.MOVIE: "🎥 Film",
            AnimeType.OVA: "💿 OVA",
            AnimeType.SPECIAL: "✨ Maxsus qism",
        }[self]


class AgeRestriction(str, Enum):
    """Yosh cheklovi."""

    ALL_AGES = "0+"
    TEEN = "13+"
    MATURE = "16+"
    ADULT = "18+"


class WatchStatus(str, Enum):
    """Bookmark folder / watch-list holati (#53, #9-11)."""

    WATCHING = "watching"
    COMPLETED = "completed"
    DROPPED = "dropped"
    PLAN_TO_WATCH = "plan_to_watch"

    @property
    def label_uz(self) -> str:
        return {
            WatchStatus.WATCHING: "▶️ Ko'rilyapti",
            WatchStatus.COMPLETED: "✅ Tugallangan",
            WatchStatus.DROPPED: "🗑 Tashlab yuborilgan",
            WatchStatus.PLAN_TO_WATCH: "📝 Rejalashtirilgan",
        }[self]


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogAction(str, Enum):
    """Audit log uchun harakat turlari."""

    ANIME_CREATE = "anime_create"
    ANIME_UPDATE = "anime_update"
    ANIME_DELETE = "anime_delete"
    ANIME_RESTORE = "anime_restore"
    EPISODE_CREATE = "episode_create"
    EPISODE_UPDATE = "episode_update"
    EPISODE_DELETE = "episode_delete"
    VIDEO_ADD = "video_add"
    VIDEO_DELETE = "video_delete"
    VIP_APPROVE = "vip_approve"
    VIP_REJECT = "vip_reject"
    VIP_CANCEL = "vip_cancel"
    ADMIN_ADD = "admin_add"
    ADMIN_REMOVE = "admin_remove"
    ADMIN_PERMISSION_CHANGE = "admin_permission_change"
    BROADCAST_SEND = "broadcast_send"
    SETTINGS_CHANGE = "settings_change"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    USER_BAN = "user_ban"
    USER_UNBAN = "user_unban"


class NotificationType(str, Enum):
    NEW_EPISODE = "new_episode"
    VIP_APPROVED = "vip_approved"
    VIP_EXPIRING = "vip_expiring"
    VIP_EXPIRED = "vip_expired"
    BROADCAST = "broadcast"
    SYSTEM = "system"


class PromoCodeType(str, Enum):
    """Promo-kod turi — #16 Promo Code va #18 VIP Coupon bitta mexanizm
    orqali ishlaydi (duplicate tizim yaratmaslik uchun)."""

    VIP_DAYS = "vip_days"
    COINS = "coins"


class Permission(str, Enum):
    """Oddiy adminlar uchun granular ruxsatlar."""

    ANIME_ADD = "anime_add"
    ANIME_EDIT = "anime_edit"
    ANIME_DELETE = "anime_delete"
    VIDEO_ADD = "video_add"
    VIDEO_DELETE = "video_delete"
    BROADCAST_SEND = "broadcast_send"
    VIP_APPROVE = "vip_approve"
    SUBSCRIPTION_MANAGE = "subscription_manage"
    BACKUP_CREATE = "backup_create"
    LOGS_VIEW = "logs_view"
    COLLECTION_MANAGE = "collection_manage"
    PROMO_MANAGE = "promo_manage"
    SCHEDULE_MANAGE = "schedule_manage"
    CONTENT_MANAGE = "content_manage"
    POLL_MANAGE = "poll_manage"
    USER_BAN = "user_ban"
    REQUEST_MANAGE = "request_manage"
    COMMENT_MODERATE = "comment_moderate"
    USER_LOOKUP = "user_lookup"

    @classmethod
    def all(cls) -> list["Permission"]:
        return list(cls)
