"""``aliases.json`` — anime uchun muqobil nomlar (qidiruv sifatini oshirish).

Fayl DICT ko'rinishida: {"<anime_code>": ["alias1", "alias2", ...]}
"""

from __future__ import annotations

from database.json_manager import JsonManager


class AliasRepository:
    def __init__(self, manager: JsonManager) -> None:
        self._manager = manager

    async def get_aliases(self, anime_code: str) -> list[str]:
        data = await self._manager.read("aliases.json", default={})
        return data.get(anime_code, [])

    async def add_alias(self, anime_code: str, alias: str) -> None:
        def _updater(data: dict) -> dict:
            aliases = data.get(anime_code, [])
            if alias not in aliases:
                aliases.append(alias)
            data[anime_code] = aliases
            return data

        await self._manager.update("aliases.json", _updater, default={})

    async def all_aliases(self) -> dict[str, list[str]]:
        return await self._manager.read("aliases.json", default={})
