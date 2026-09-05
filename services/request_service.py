"""Anime so'rovi va bug-report logikasi."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from database.models.request import AnimeRequest, BugReport
from database.repositories.request_repository import AnimeRequestRepository, BugReportRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class AnimeRequestService:
    def __init__(self, requests: AnimeRequestRepository) -> None:
        self._requests = requests

    async def submit(self, user_id: int, title: str, note: str = "") -> tuple[AnimeRequest, bool]:
        """So'rov yuboradi. Agar bir xil nomdagi so'rov allaqachon
        kutilayotgan bo'lsa, yangi yozuv yaratmasdan unga ovoz beradi
        (adminlar bir xil so'rovni bir necha marta ko'rmasligi uchun).

        Qaytaradi: ``(request, yangi_yaratildimi)``.
        """

        existing = await self._requests.find_similar_pending(title)
        if existing:
            if user_id not in existing.upvoted_by and user_id != existing.user_id:
                updated = await self._requests.upvote(existing.id, user_id)
                return (updated or existing), False
            return existing, False

        request = AnimeRequest(id=str(uuid.uuid4()), user_id=user_id, title=title, note=note)
        saved, added = await self._requests.add_if_absent(request)
        return (saved if added else request), added

    async def list_pending(self) -> list[AnimeRequest]:
        pending = await self._requests.list_pending()
        # Ko'p ovoz olganlar birinchi bo'lib ko'rinsin — adminlar eng
        # so'raladigan animelarni birinchi navbatda ko'radi.
        return sorted(pending, key=lambda r: len(r.upvoted_by), reverse=True)

    async def decide(
        self, request_id: str, status: str, admin_id: int, comment: str | None = None
    ) -> AnimeRequest | None:
        return await self._requests.update(
            request_id,
            {
                "status": status,
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "decided_by": admin_id,
                "admin_comment": comment,
            },
        )

    async def list_for_user(self, user_id: int) -> list[AnimeRequest]:
        return await self._requests.list_for_user(user_id)


class BugReportService:
    def __init__(self, reports: BugReportRepository) -> None:
        self._reports = reports

    async def submit(self, user_id: int, text: str, anime_code: str | None = None) -> BugReport:
        report = BugReport(id=str(uuid.uuid4()), user_id=user_id, text=text[:1000], anime_code=anime_code)
        await self._reports.add(report)
        return report

    async def list_open(self) -> list[BugReport]:
        return await self._reports.list_open()

    async def resolve(self, report_id: str, admin_id: int) -> BugReport | None:
        return await self._reports.update(
            report_id,
            {
                "status": "resolved",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolved_by": admin_id,
            },
        )
