"""JSON fayllarni tekshirish/tozalash logikasi — #55 JSON Optimizer,
#56 Automatic JSON Repair, #57 Automatic Duplicate Cleaner.
"""

from __future__ import annotations

import json as json_lib

from database.json_manager import JsonManager
from database.schemas import ALL_JSON_FILES, get_default
from utils.logger import get_logger

logger = get_logger(__name__)


class MaintenanceService:
    def __init__(self, manager: JsonManager) -> None:
        self._manager = manager

    async def repair_all(self) -> dict[str, str]:
        """#56 Automatic JSON Repair — har bir faylni o'qishga urinadi.

        Buzilgan (parse qilinmaydigan) fayl topilsa, uni standart bo'sh
        qiymat bilan almashtiradi (avval fayl backup qilinadi). Har bir
        fayl uchun natija (``"ok"`` yoki ``"repaired"``) qaytaradi.
        """

        results: dict[str, str] = {}
        for filename in ALL_JSON_FILES:
            try:
                await self._manager.read(filename, use_cache=False)
                results[filename] = "ok"
            except Exception as exc:  # noqa: BLE001 — JsonCorruptedError va h.k.
                logger.warning("Buzilgan fayl aniqlandi: %s (%s)", filename, exc)
                try:
                    await self._manager.backup(filename)
                except Exception:  # noqa: BLE001
                    pass
                await self._manager.write(filename, get_default(filename))
                results[filename] = "repaired"
        return results

    async def remove_duplicates(self, filename: str, id_field: str = "id") -> int:
        """#57 Automatic Duplicate Cleaner — bitta LIST-fayldagi bir xil
        ``id_field`` qiymatiga ega takroriy yozuvlarni olib tashlaydi
        (birinchisini saqlab qoladi). O'chirilgan yozuvlar sonini qaytaradi.
        """

        removed_count = 0

        def _updater(data):
            nonlocal removed_count
            if not isinstance(data, list):
                return data
            seen = set()
            cleaned = []
            for entry in data:
                key = entry.get(id_field)
                if key in seen:
                    removed_count += 1
                    continue
                seen.add(key)
                cleaned.append(entry)
            return cleaned

        await self._manager.update(filename, _updater, default=[])
        return removed_count

    async def remove_duplicates_all(self) -> dict[str, int]:
        """Barcha LIST-turidagi fayllar uchun duplicate-tozalashni bajaradi."""

        id_field_map = {
            "anime.json": "code",
            "promo_codes.json": "code",
        }
        results: dict[str, int] = {}
        for filename in ALL_JSON_FILES:
            default = get_default(filename)
            if not isinstance(default, list):
                continue
            id_field = id_field_map.get(filename, "id")
            removed = await self.remove_duplicates(filename, id_field)
            if removed:
                results[filename] = removed
        return results

    async def optimize_trash(self, keep_days: int = 30) -> int:
        """#55 JSON Optimizer — ``is_deleted=True`` bo'lgan va
        ``keep_days``dan eski yozuvlarni animelar faylidan butunlay
        o'chiradi (soft-delete → hard-delete, joy bo'shatish uchun).
        """

        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
        removed_count = 0

        def _updater(data: list[dict]) -> list[dict]:
            nonlocal removed_count
            cleaned = []
            for entry in data:
                if entry.get("is_deleted"):
                    created_at = entry.get("created_at") or entry.get("updated_at")
                    if created_at:
                        try:
                            ts = datetime.fromisoformat(created_at)
                            if ts < cutoff:
                                removed_count += 1
                                continue
                        except ValueError:
                            pass
                cleaned.append(entry)
            return cleaned

        await self._manager.update("anime.json", _updater, default=[])
        return removed_count

    async def file_sizes(self) -> dict[str, int]:
        """Har bir JSON faylning disk hajmini (bayt) qaytaradi (Health
        Dashboard uchun)."""

        sizes = {}
        for filename in ALL_JSON_FILES:
            size = self._manager.file_size(filename)
            if size:
                sizes[filename] = size
        return sizes
