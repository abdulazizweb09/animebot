"""Admin harakatlarini ``logs.json`` ga yozib boruvchi audit-log xizmati."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from config.enums import LogAction
from database.json_manager import JsonManager
from utils.logger import get_logger

logger = get_logger(__name__)


class AuditLogService:
    def __init__(self, manager: JsonManager) -> None:
        self._manager = manager

    async def log(
        self, actor_id: int, action: LogAction, details: dict | None = None
    ) -> None:
        entry = {
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "action": action.value,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        def _updater(data: list[dict]) -> list[dict]:
            data.append(entry)
            return data

        await self._manager.update("logs.json", _updater, default=[])
        logger.info("AUDIT: actor=%s action=%s details=%s", actor_id, action.value, details)

    async def recent(self, limit: int = 50) -> list[dict]:
        logs = await self._manager.read("logs.json", default=[])
        return list(reversed(logs))[:limit]
