"""Har bir JSON fayl uchun standart (bo'sh) struktura.

``main.py`` ishga tushganda ``JsonManager.auto_create`` shu yerdagi
qiymatlar bilan chaqiriladi — shunda bot birinchi marta ishga tushganda ham
"fayl topilmadi" degan xato bo'lmaydi.

Har bir fayl uchun kalit ro'yxati va default qiymat ``JSON_SCHEMAS`` lug'atida
markazlashtirilgan — yangi fayl qo'shish uchun shu yerga bitta qator
qo'shish kifoya.
"""

from __future__ import annotations

from typing import Any

JsonType = dict[str, Any] | list[Any]

# Ko'pchilik fayl "ro'yxat" (list) ko'rinishida saqlanadi — har bir element
# alohida yozuv (masalan, bitta anime, bitta user). Ba'zilari "lug'at"
# (dict) — masalan, settings.json global sozlamalar uchun.

JSON_SCHEMAS: dict[str, JsonType] = {
    "users.json": [],
    "admins.json": [],
    "permissions.json": {},  # {"<admin_id>": ["anime_add", "anime_edit", ...]}
    "anime.json": [],
    "episodes.json": [],
    "videos.json": [],
    "vip.json": [],  # aktiv/tugagan VIP obunalar tarixi
    "payments.json": [],
    "subscriptions.json": [],  # majburiy obuna kanallari ro'yxati
    "broadcasts.json": [],
    "settings.json": {
        "maintenance_mode": False,
        "force_subscription_enabled": True,
        "ai_enabled": True,
        "registration_enabled": True,
        "default_language": "uz",
    },
    "languages.json": {},  # runtime'da qo'shiladigan qo'shimcha tarjimalar
    "logs.json": [],  # audit log yozuvlari
    "analytics.json": {
        "total_starts": 0,
        "total_searches": 0,
        "total_ai_requests": 0,
        "daily": {},
    },
    "events.json": [],  # windowed analytics: {id, event_type, user_id, anime_code, meta, timestamp}
    "collections.json": [],  # Anime Collection / Franchise guruhlari
    "achievements.json": [],  # foydalanuvchi badge/yutuqlari
    "referrals.json": [],  # referal tizimi yozuvlari
    "promo_codes.json": [],  # promo-kod va VIP kuponlar
    "economy.json": {},  # {"<user_id>": {"coins": 0, "xp": 0, "level": 1, "last_daily": None}}
    "schedule.json": [],  # anime chiqish jadvali (kalendar/eslatmalar uchun)
    "polls.json": [],
    "quizzes.json": [],
    "favorites.json": [],  # [{"user_id": ..., "anime_code": ..., "added_at": ...}]
    "history.json": [],  # ko'rish tarixi
    "watch_later.json": [],
    "watchlist.json": [],  # bookmark folders: watching/completed/dropped/plan_to_watch
    "ratings.json": [],
    "comments.json": [],
    "notifications.json": [],
    "ai_history.json": [],  # {"user_id": ..., "messages": [...]}
    "backup.json": {
        "last_backup_at": None,
        "backup_count": 0,
        "history": [],
    },
    "trash.json": [],  # o'chirilgan animelar (soft-delete)
    "categories.json": [],
    "characters.json": [],  # #25-26 Character/Voice Actor Search, #40 Gallery
    "media_gallery.json": [],  # #41 Wallpaper, #42 Trailer
    "news.json": [],  # #43 Anime News, #44 Announcements
    "aliases.json": {},  # {"anime_code": ["alias1", "alias2", ...]}
    "search_history.json": [],
    "anime_requests.json": [],  # foydalanuvchi anime so'rovlari
    "bug_reports.json": [],  # muammo/xato xabarlari
    "system.json": {
        "started_at": None,
        "version": "1.0.0",
        "last_health_check": None,
    },
}


def get_default(filename: str) -> JsonType:
    """Berilgan fayl nomi uchun standart qiymatni qaytaradi.

    Ro'yxatda yo'q nom uchun bo'sh ro'yxat qaytariladi (xavfsiz default).
    """

    key = filename if filename.endswith(".json") else f"{filename}.json"
    default = JSON_SCHEMAS.get(key, [])
    # Mutable default'larni tashqariga "ulashib" yubormaslik uchun nusxa
    if isinstance(default, dict):
        return dict(default)
    if isinstance(default, list):
        return list(default)
    return default


ALL_JSON_FILES: tuple[str, ...] = tuple(JSON_SCHEMAS.keys())
