"""Database package.

``get_json_manager()`` butun bot davomida bitta ``JsonManager`` instansiyasini
qaytaradi (singleton) — shu orqali barcha repository/servicelar bir xil
lock/cache holatidan foydalanadi.
"""

from __future__ import annotations

from functools import lru_cache

from config.settings import get_settings
from database.json_manager import JsonManager


@lru_cache(maxsize=1)
def get_json_manager() -> JsonManager:
    settings = get_settings()
    return JsonManager(
        base_dir=settings.json_dir,
        backup_dir=settings.backup_path,
        cache_ttl_seconds=300,
        cache_max_entries=512,
    )


async def bootstrap_json_files() -> None:
    """Bot ishga tushishida barcha kerakli JSON fayllarni auto-create qiladi."""

    from database.schemas import ALL_JSON_FILES, get_default

    manager = get_json_manager()
    for filename in ALL_JSON_FILES:
        await manager.auto_create(filename, get_default(filename))


__all__ = ["get_json_manager", "bootstrap_json_files"]
