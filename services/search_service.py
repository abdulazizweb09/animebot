"""Anime nomi bo'yicha fuzzy qidiruv logikasi (rapidfuzz asosida).

Endi qidiruv nafaqat asosiy nom (``title_uz``), balki original nom
(``title_original``) va admin qo'shgan muqobil nomlar (aliases) bo'yicha
ham ishlaydi — masalan "AoT" deb qidirilsa "Attack on Titan" topiladi.
"""

from __future__ import annotations

import uuid

from rapidfuzz import fuzz, process

from config.constants import CONSTANTS
from database.models.anime import Anime
from database.repositories.alias_repository import AliasRepository
from database.repositories.anime_repository import AnimeRepository
from database.repositories.search_history_repository import (
    SearchHistoryEntry,
    SearchHistoryRepository,
)


class SearchService:
    def __init__(
        self,
        animes: AnimeRepository,
        aliases: AliasRepository | None = None,
        history: SearchHistoryRepository | None = None,
    ) -> None:
        self._animes = animes
        self._aliases = aliases
        self._history = history

    async def _build_search_index(self, all_animes: list[Anime]) -> dict[str, str]:
        """``{"<qidiruv_kaliti>": "<anime_code>"}`` — har bir anime uchun
        asosiy nom, original nom va barcha aliaslar alohida kalit sifatida
        qo'shiladi, shunda foydalanuvchi ularning har biri bo'yicha topa oladi.
        """

        index: dict[str, str] = {}
        alias_map = await self._aliases.all_aliases() if self._aliases else {}

        for a in all_animes:
            index[f"{a.code}::title"] = a.title_uz
            if a.title_original:
                index[f"{a.code}::orig"] = a.title_original
            for i, alias in enumerate(alias_map.get(a.code, [])):
                index[f"{a.code}::alias{i}"] = alias

        return index

    async def search(self, query: str, user_id: int | None = None) -> list[Anime]:
        query = query.strip()
        if len(query) < CONSTANTS.MIN_SEARCH_QUERY_LENGTH:
            return []

        all_animes = await self._animes.all()
        if not all_animes:
            return []

        search_index = await self._build_search_index(all_animes)
        matches = process.extract(
            query,
            search_index,
            scorer=fuzz.WRatio,
            score_cutoff=CONSTANTS.FUZZY_SEARCH_THRESHOLD,
            limit=CONSTANTS.MAX_SEARCH_RESULTS * 3,  # bir anime bir necha marta topilishi mumkin
        )

        by_code = {a.code: a for a in all_animes}
        seen_codes: set[str] = set()
        results: list[Anime] = []
        for _matched_text, _score, composite_key in matches:
            code = composite_key.split("::", 1)[0]
            if code in seen_codes or code not in by_code:
                continue
            seen_codes.add(code)
            results.append(by_code[code])
            if len(results) >= CONSTANTS.MAX_SEARCH_RESULTS:
                break

        if self._history and user_id is not None:
            entry = SearchHistoryEntry(
                id=str(uuid.uuid4()), user_id=user_id, query=query, results_count=len(results)
            )
            await self._history.add(entry)

        return results

    async def recent_searches(self, user_id: int, limit: int = 10) -> list[str]:
        if self._history is None:
            return []
        entries = await self._history.recent_for_user(user_id, limit)
        return [e.query for e in entries]
