"""``economy.json`` repository — DICT ko'rinishidagi fayl (user_id -> profil).

``BaseRepository`` faqat LIST ko'rinishidagi fayllar uchun mo'ljallangan
(har bir yozuv alohida elementga ega). ``economy.json`` esa
``{"<user_id>": {...}}`` ko'rinishida saqlanadi, shuning uchun bu klass
``BaseRepository``dan meros olmaydi va to'g'ridan-to'g'ri ``JsonManager``
bilan ishlaydi.
"""

from __future__ import annotations

from datetime import datetime, timezone

from database.json_manager import JsonManager
from database.models.economy import EconomyProfile


class EconomyRepository:
    def __init__(self, manager: JsonManager) -> None:
        self._manager = manager

    async def get(self, user_id: int) -> EconomyProfile:
        """Profilni qaytaradi, mavjud bo'lmasa standart (bo'sh) profil
        qaytaradi (diskka yozmaydi — birinchi ``save`` da yoziladi).
        """

        data = await self._manager.read("economy.json", default={})
        raw = data.get(str(user_id))
        if raw is None:
            return EconomyProfile(user_id=user_id)
        return EconomyProfile.from_dict(user_id, raw)

    async def save(self, profile: EconomyProfile) -> None:
        profile.updated_at = datetime.now(timezone.utc).isoformat()

        def _updater(data: dict) -> dict:
            data[str(profile.user_id)] = profile.to_dict()
            return data

        await self._manager.update("economy.json", _updater, default={})

    async def top_by_xp(self, limit: int = 10) -> list[EconomyProfile]:
        data = await self._manager.read("economy.json", default={})
        profiles = [
            EconomyProfile.from_dict(int(uid), raw) for uid, raw in data.items()
        ]
        return sorted(profiles, key=lambda p: p.xp, reverse=True)[:limit]

    async def top_by_coins(self, limit: int = 10) -> list[EconomyProfile]:
        data = await self._manager.read("economy.json", default={})
        profiles = [
            EconomyProfile.from_dict(int(uid), raw) for uid, raw in data.items()
        ]
        return sorted(profiles, key=lambda p: p.coins, reverse=True)[:limit]

    async def try_spend(self, user_id: int, amount: int) -> bool:
        """Tangani BITTA atomik lock ostida yechadi — agar mablag' yetarli
        bo'lmasa, hech narsa o'zgartirmaydi. Bu ikkita tez-tez sotib olish
        so'rovi bir vaqtda kelib, ikkalasi ham balansni "yetarli" deb
        topib, balansni manfiy qilib qo'yishining oldini oladi (xuddi
        promo-kod va epizod-raqamlash tuzatishlaridagi kabi tamoyil).
        """

        result_holder: dict[str, bool] = {"success": False}

        def _updater(data: dict) -> dict:
            key = str(user_id)
            profile_raw = data.get(key, {})
            current_coins = profile_raw.get("coins", 0)
            if current_coins < amount:
                result_holder["success"] = False
                return data
            profile_raw["coins"] = current_coins - amount
            profile_raw["user_id"] = user_id
            data[key] = profile_raw
            result_holder["success"] = True
            return data

        await self._manager.update("economy.json", _updater, default={})
        return result_holder["success"]
