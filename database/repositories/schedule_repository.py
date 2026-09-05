"""``schedule.json`` repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database.json_manager import JsonManager
from database.models.schedule import ScheduleEntry
from database.repositories.base_repository import BaseRepository


class ScheduleRepository(BaseRepository[ScheduleEntry]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "schedule.json", ScheduleEntry, id_field="id")

    async def list_for_anime(self, anime_code: str) -> list[ScheduleEntry]:
        entries = await self.find_all(lambda e: e.get("anime_code") == anime_code)
        return sorted(entries, key=lambda e: e.release_at)

    async def next_for_anime(self, anime_code: str) -> ScheduleEntry | None:
        """Berilgan anime uchun ENG YAQIN kelajakdagi (hali chiqmagan)
        epizodni qaytaradi — #22 Countdown uchun.
        """

        entries = await self.list_for_anime(anime_code)
        now = datetime.now(timezone.utc)
        future = [e for e in entries if e.release_datetime() > now]
        return future[0] if future else None

    async def today(self) -> list[ScheduleEntry]:
        """#20 Anime Calendar — bugun chiqadigan epizodlar."""

        entries = await self.all()
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return sorted(
            [e for e in entries if today_start <= e.release_datetime() < today_end],
            key=lambda e: e.release_at,
        )

    async def upcoming(self, days: int = 7) -> list[ScheduleEntry]:
        entries = await self.all()
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)
        return sorted(
            [e for e in entries if now <= e.release_datetime() <= cutoff],
            key=lambda e: e.release_at,
        )

    async def due_for_notification(self, window: str) -> list[ScheduleEntry]:
        """``window`` — "1day" | "1hour" | "30min". Hali xabar berilmagan va
        vaqti yetgan yozuvlarni qaytaradi (fon vazifasi uchun).
        """

        thresholds = {
            "1day": timedelta(days=1),
            "1hour": timedelta(hours=1),
            "30min": timedelta(minutes=30),
        }
        flag_field = f"notified_{window}"
        threshold = thresholds[window]

        entries = await self.all()
        now = datetime.now(timezone.utc)
        result = []
        for e in entries:
            if getattr(e, flag_field):
                continue
            remaining = e.release_datetime() - now
            if timedelta(0) < remaining <= threshold:
                result.append(e)
        return result

    async def mark_notified(self, entry_id: str, window: str) -> None:
        await self.update(entry_id, {f"notified_{window}": True})

    async def mark_released_if_due(self) -> list[ScheduleEntry]:
        entries = await self.all()
        now = datetime.now(timezone.utc)
        released = []
        for e in entries:
            if not e.is_released and e.release_datetime() <= now:
                await self.update(e.id, {"is_released": True})
                released.append(e)
        return released
