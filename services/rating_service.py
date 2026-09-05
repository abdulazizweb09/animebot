"""Yulduzli baholash (rating) va izohlar (comments) logikasi."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from database.models.rating import Comment, UserRating
from database.repositories.anime_repository import AnimeRepository
from database.repositories.rating_repository import CommentRepository, RatingRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class RatingService:
    def __init__(self, ratings: RatingRepository, animes: AnimeRepository) -> None:
        self._ratings = ratings
        self._animes = animes

    async def rate(
        self, user_id: int, anime_code: str, score: int, review: str = ""
    ) -> UserRating:
        """Foydalanuvchi bahosini qo'yadi yoki yangilaydi.

        Agar foydalanuvchi oldin baho qo'ygan bo'lsa — eski baho anime
        umumiy statistikasidan ayiriladi, yangisi qo'shiladi (statistika
        buzilmasligi uchun).
        """

        score = max(1, min(10, score))
        existing = await self._ratings.get_user_rating(user_id, anime_code)

        if existing:
            # Eski bahoni umumiy statistikadan olib tashlab, yangisini qo'shamiz
            anime = await self._animes.get_by_code(anime_code)
            if anime:
                new_sum = anime.rating_sum - existing.score + score
                await self._animes.update(anime_code, {"rating_sum": new_sum})

            updated = UserRating(
                id=existing.id,
                user_id=user_id,
                anime_code=anime_code,
                score=score,
                review=review or existing.review,
                created_at=existing.created_at,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            await self._ratings.replace(updated)
            return updated

        rating = UserRating(
            id=str(uuid.uuid4()), user_id=user_id, anime_code=anime_code, score=score, review=review
        )
        await self._ratings.add(rating)
        await self._animes.add_rating(anime_code, score)
        return rating

    async def get_user_rating(self, user_id: int, anime_code: str) -> UserRating | None:
        return await self._ratings.get_user_rating(user_id, anime_code)

    async def anime_stats(self, anime_code: str) -> dict:
        return await self._ratings.anime_stats(anime_code)

    async def list_for_user(self, user_id: int) -> list[UserRating]:
        return await self._ratings.list_by_user(user_id)


class CommentService:
    def __init__(self, comments: CommentRepository) -> None:
        self._comments = comments

    async def add_comment(self, user_id: int, anime_code: str, text: str) -> Comment:
        text = text.strip()[:1000]  # himoya: haddan tashqari uzun izohni kesish
        comment = Comment(id=str(uuid.uuid4()), user_id=user_id, anime_code=anime_code, text=text)
        await self._comments.add(comment)
        return comment

    async def list_for_anime(self, anime_code: str, limit: int = 10) -> list[Comment]:
        return await self._comments.list_for_anime(anime_code, limit)

    async def toggle_like(self, comment_id: str, user_id: int) -> Comment | None:
        return await self._comments.like(comment_id, user_id)

    async def delete_comment(self, comment_id: str, requester_id: int, is_admin: bool) -> bool:
        comment = await self._comments.get(comment_id)
        if comment is None:
            return False
        if comment.user_id != requester_id and not is_admin:
            return False
        return await self._comments.soft_delete(comment_id)

    async def recent_for_moderation(self, limit: int = 20) -> list[Comment]:
        """#Moderatsiya — barcha animelar bo'yicha so'nggi izohlar, admin
        panelda ko'rib chiqish uchun."""

        return await self._comments.recent_all(limit)

    async def report_comment(self, comment_id: str, user_id: int) -> Comment | None:
        return await self._comments.report(comment_id, user_id)

    async def list_most_reported(self, limit: int = 20) -> list[Comment]:
        return await self._comments.most_reported(limit)
