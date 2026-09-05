"""Anime Calendar / Schedule Notification / Countdown logikasi (#20-22)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from database.models.schedule import ScheduleEntry
from database.repositories.anime_repository import AnimeRepository
from database.repositories.schedule_repository import ScheduleRepository
from utils.logger import get_logger

logger = get_logger(__name__)


def _format_timedelta_uz(remaining) -> str:
    total_seconds = int(remaining.total_seconds())
    if total_seconds <= 0:
        return "chiqdi"

    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days} kun")
    if hours:
        parts.append(f"{hours} soat")
    if minutes and not days:
        parts.append(f"{minutes} daqiqa")
    return " ".join(parts) if parts else "1 daqiqadan kam"


class ScheduleService:
    def __init__(self, schedule: ScheduleRepository, animes: AnimeRepository) -> None:
        self._schedule = schedule
        self._animes = animes

    async def create_entry(
        self, anime_code: str, episode_number: int, release_at: datetime, created_by: int
    ) -> ScheduleEntry:
        entry = ScheduleEntry(
            id=str(uuid.uuid4()),
            anime_code=anime_code,
            episode_number=episode_number,
            release_at=release_at.astimezone(timezone.utc).isoformat(),
            created_by=created_by,
        )
        await self._schedule.add(entry)
        logger.info(
            "Jadval yozuvi qo'shildi: %s #%s -> %s", anime_code, episode_number, entry.release_at
        )
        return entry

    async def today_releases(self) -> list[tuple[ScheduleEntry, object]]:
        """#20 Anime Calendar — bugungi chiqishlar, anime obyekti bilan birga."""

        entries = await self._schedule.today()
        result = []
        for e in entries:
            anime = await self._animes.get_by_code(e.anime_code)
            result.append((e, anime))
        return result

    async def upcoming_releases(self, days: int = 7) -> list[tuple[ScheduleEntry, object]]:
        entries = await self._schedule.upcoming(days)
        result = []
        for e in entries:
            anime = await self._animes.get_by_code(e.anime_code)
            result.append((e, anime))
        return result

    async def countdown_text(self, anime_code: str) -> str | None:
        """#22 Anime Countdown — keyingi epizodgacha qolgan vaqt matni."""

        entry = await self._schedule.next_for_anime(anime_code)
        if entry is None:
            return None
        remaining = entry.time_remaining()
        return f"{entry.episode_number}-qism: {_format_timedelta_uz(remaining)} qoldi"
