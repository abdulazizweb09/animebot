"""Analytics — har bir user/AI amalini voqea (event) sifatida yozib boradi.

``events.json`` — vaqt-oynali (24s/7k/30k) hisob-kitoblar (Trending, va h.k.)
uchun xom voqealar ro'yxati. ``analytics.json`` — umumlashtirilgan
sanoqchilar (total_starts va h.k., mavjud tizim).

Bu servis mavjud ``analytics.json`` schemasiga tegmaydi — faqat yangi
``events.json`` fayli bilan ishlaydi (qo'shimcha, additive imkoniyat).
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from database.json_manager import JsonManager
from utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    def __init__(self, manager: JsonManager) -> None:
        self._manager = manager

    async def log_event(
        self,
        event_type: str,
        user_id: int | None = None,
        anime_code: str | None = None,
        meta: dict | None = None,
    ) -> None:
        entry = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "user_id": user_id,
            "anime_code": anime_code,
            "meta": meta or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        def _updater(data: list[dict]) -> list[dict]:
            data.append(entry)
            return data

        await self._manager.update("events.json", _updater, default=[])

    async def _events_since(self, event_type: str, hours: int) -> list[dict]:
        events = await self._manager.read("events.json", default=[])
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = []
        for e in events:
            if e.get("event_type") != event_type:
                continue
            try:
                ts = datetime.fromisoformat(e["timestamp"])
            except (KeyError, ValueError):
                continue
            if ts >= cutoff:
                result.append(e)
        return result

    async def trending_anime_codes(
        self, hours: int = 24, limit: int = 10
    ) -> list[tuple[str, int]]:
        """``(anime_code, ko'rishlar_soni)`` — eng ko'p ko'rilgan animelar,
        so'nggi ``hours`` soat ichida.
        """

        events = await self._events_since("anime_view", hours)
        counter: Counter[str] = Counter(
            e["anime_code"] for e in events if e.get("anime_code")
        )
        return counter.most_common(limit)

    async def count_since(self, event_type: str, hours: int) -> int:
        events = await self._events_since(event_type, hours)
        return len(events)
