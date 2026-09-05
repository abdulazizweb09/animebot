"""#3 Anime Recommendation Engine.

Oddiy random emas — quyidagi omillar asosida ballash (scoring) tizimi:
    • Genre  — foydalanuvchi ko'p ko'rgan/sevimli janrlar ustuvor
    • Studio — foydalanuvchi ko'p ko'rgan studiyalar ustuvor
    • Rating — yuqori baholangan animelar ustuvor
    • Watching History — allaqachon ko'rilgan animelar tavsiya qilinmaydi
    • Favorites — sevimlilardagi janr/studiyalar og'irlik beradi

AI (Gemini) mavjud bo'lsa, top-N nomzod orasidan eng mosini tabiiy tilda
tushuntirish bilan birga tanlab beradi — lekin bu ixtiyoriy qatlam, asosiy
ballash tizimi AI'siz ham to'liq ishlaydi.
"""

from __future__ import annotations

from collections import Counter

from database.models.anime import Anime
from database.repositories.anime_repository import AnimeRepository
from database.repositories.interaction_repository import (
    FavoriteRepository,
    HistoryRepository,
)
from utils.logger import get_logger

logger = get_logger(__name__)

_GENRE_WEIGHT = 3.0
_STUDIO_WEIGHT = 2.0
_RATING_WEIGHT = 1.0
_FAVORITE_BONUS = 5.0


class RecommendationService:
    def __init__(
        self,
        animes: AnimeRepository,
        favorites: FavoriteRepository,
        history: HistoryRepository,
    ) -> None:
        self._animes = animes
        self._favorites = favorites
        self._history = history

    async def _build_user_taste_profile(
        self, user_id: int
    ) -> tuple[Counter, Counter, set[str]]:
        """Foydalanuvchi tarixi va sevimlilari asosida janr/studiya
        og'irliklarini va ko'rilgan anime kodlarini quradi.
        """

        genre_weights: Counter = Counter()
        studio_weights: Counter = Counter()
        watched_codes: set[str] = set()

        history_entries = await self._history.list_for_user(user_id, limit=200)
        for entry in history_entries:
            watched_codes.add(entry.anime_code)
            anime = await self._animes.get_by_code(entry.anime_code)
            if anime:
                for genre in anime.genres:
                    genre_weights[genre] += 1.0
                if anime.studio:
                    studio_weights[anime.studio] += 1.0

        favorites = await self._favorites.list_for_user(user_id)
        for fav in favorites:
            anime = await self._animes.get_by_code(fav.anime_code)
            if anime:
                for genre in anime.genres:
                    genre_weights[genre] += _FAVORITE_BONUS
                if anime.studio:
                    studio_weights[anime.studio] += _FAVORITE_BONUS

        return genre_weights, studio_weights, watched_codes

    def _score_anime(
        self, anime: Anime, genre_weights: Counter, studio_weights: Counter
    ) -> float:
        score = 0.0
        for genre in anime.genres:
            score += genre_weights.get(genre, 0.0) * _GENRE_WEIGHT
        if anime.studio:
            score += studio_weights.get(anime.studio, 0.0) * _STUDIO_WEIGHT
        score += anime.average_rating * _RATING_WEIGHT
        return score

    async def recommend(self, user_id: int, limit: int = 10) -> list[Anime]:
        """Foydalanuvchiga shaxsiylashtirilgan tavsiyalar qaytaradi.

        Agar foydalanuvchida hali tarix/sevimli bo'lmasa (yangi user),
        eng yuqori baholangan animelarni qaytaradi (cold-start holati).
        """

        genre_weights, studio_weights, watched_codes = await self._build_user_taste_profile(
            user_id
        )

        all_animes = await self._animes.all()
        candidates = [a for a in all_animes if a.code not in watched_codes]

        if not genre_weights and not studio_weights:
            # Cold-start: hali hech narsa ko'rmagan/sevimli qilmagan user
            return sorted(candidates, key=lambda a: a.average_rating, reverse=True)[:limit]

        scored = [
            (self._score_anime(a, genre_weights, studio_weights), a) for a in candidates
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [a for _score, a in scored[:limit]]

    async def similar_to(self, anime_code: str, limit: int = 10) -> list[Anime]:
        """Berilgan animega o'xshash (bir xil janr/studiya) boshqa animelar
        — anime kartochkasida "shunga o'xshash" bo'limi uchun.
        """

        source = await self._animes.get_by_code(anime_code)
        if source is None:
            return []

        genre_weights = Counter({g: 1.0 for g in source.genres})
        studio_weights = Counter({source.studio: 1.0}) if source.studio else Counter()

        all_animes = await self._animes.all()
        candidates = [a for a in all_animes if a.code != anime_code]

        scored = [
            (self._score_anime(a, genre_weights, studio_weights), a)
            for a in candidates
        ]
        scored = [pair for pair in scored if pair[0] > 0]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [a for _score, a in scored[:limit]]
