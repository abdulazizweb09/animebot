"""Loyihada ishlatiladigan doimiy qiymatlar (magic number/string emas)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Constants:
    """Har xil joyda hardcode bo'lishi mumkin bo'lgan qiymatlar shu yerda."""

    # Pagination
    ANIME_PER_PAGE: int = 8
    SEARCH_RESULTS_PER_PAGE: int = 8
    HISTORY_PER_PAGE: int = 10
    FAVORITES_PER_PAGE: int = 8
    USERS_PER_PAGE: int = 10
    LOGS_PER_PAGE: int = 15

    # Search
    FUZZY_SEARCH_THRESHOLD: int = 60  # 0-100, rapidfuzz score_cutoff
    MAX_SEARCH_RESULTS: int = 50
    MIN_SEARCH_QUERY_LENGTH: int = 2

    # Cache
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 512

    # AI
    AI_MAX_HISTORY_MESSAGES: int = 20
    AI_MAX_OUTPUT_TOKENS: int = 1024
    AI_TEMPERATURE: float = 0.8
    AI_CONTEXT_ANIME_LIMIT: int = 15
    AI_DAILY_LIMIT: int = 30

    # Broadcast
    BROADCAST_BATCH_SIZE: int = 25
    BROADCAST_DELAY_SECONDS: float = 0.05

    # Upload queue
    UPLOAD_MAX_CONCURRENT: int = 5
    UPLOAD_MAX_RETRIES: int = 3
    UPLOAD_RETRY_DELAY_SECONDS: float = 2.0

    # Backup
    BACKUP_KEEP_LAST_N: int = 10
    BACKUP_AUTO_INTERVAL_HOURS: int = 6

    # Trash
    TRASH_AUTO_PURGE_DAYS: int = 30

    # VIP
    VIP_EXPIRY_WARNING_DAYS: tuple = field(default_factory=lambda: (3, 1))

    # Callback data prefixes (namespacing uchun)
    CB_ANIME: str = "anm"
    CB_EPISODE: str = "eps"
    CB_VIDEO: str = "vid"
    CB_VIP: str = "vip"
    CB_ADMIN: str = "adm"
    CB_FAV: str = "fav"
    CB_LANG: str = "lng"
    CB_PAGE: str = "pg"
    CB_CATEGORY: str = "cat"
    CB_SETTINGS: str = "set"
    CB_CONFIRM: str = "cnf"
    CB_CANCEL: str = "cxl"


CONSTANTS = Constants()
