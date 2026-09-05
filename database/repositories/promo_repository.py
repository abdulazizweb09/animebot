"""``promo_codes.json`` repository."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.promo import PromoCode
from database.repositories.base_repository import BaseRepository


class PromoRepository(BaseRepository[PromoCode]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "promo_codes.json", PromoCode, id_field="code")

    async def get_by_code(self, code: str) -> PromoCode | None:
        return await self.get(code.strip().upper())

    async def redeem(self, code: str, user_id: int) -> PromoCode | None:
        """Kodni bitta atomik lock ostida ishlatadi — bir nechta user bir
        vaqtda bir xil kodni ishlatsa ham, ``used_count`` noto'g'ri
        oshib ketmasligi (race condition) uchun.
        """

        result_holder: dict[str, dict] = {}

        def _updater(data: list[dict]) -> list[dict]:
            for entry in data:
                if entry.get("code") == code:
                    promo = PromoCode.from_dict(entry)
                    if not promo.is_usable() or user_id in promo.used_by:
                        result_holder["promo"] = None
                        return data
                    entry["used_count"] = entry.get("used_count", 0) + 1
                    entry["used_by"] = entry.get("used_by", []) + [user_id]
                    result_holder["promo"] = entry
                    return data
            result_holder["promo"] = None
            return data

        await self._manager.update(self._filename, _updater, default=[])
        raw = result_holder.get("promo")
        return PromoCode.from_dict(raw) if raw else None
