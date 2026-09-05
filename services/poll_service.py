"""Poll (#45) va Quiz (#46) servisi."""

from __future__ import annotations

import uuid

from database.models.poll import Poll, QuizQuestion
from database.repositories.economy_repository import EconomyRepository
from database.repositories.poll_repository import PollRepository, QuizRepository

QUIZ_CORRECT_XP = 15
QUIZ_CORRECT_COINS = 10


class PollService:
    def __init__(self, polls: PollRepository) -> None:
        self._polls = polls

    async def create_poll(self, question: str, options: list[str], created_by: int) -> Poll:
        poll = Poll(id=str(uuid.uuid4()), question=question, options=options, created_by=created_by)
        await self._polls.add(poll)
        return poll

    async def active_polls(self) -> list[Poll]:
        return await self._polls.active_polls()

    async def vote(self, poll_id: str, user_id: int, option_index: int) -> Poll | None:
        return await self._polls.vote(poll_id, user_id, option_index)


class QuizService:
    def __init__(self, quizzes: QuizRepository, economy: EconomyRepository) -> None:
        self._quizzes = quizzes
        self._economy = economy

    async def create_question(
        self, question: str, options: list[str], correct_index: int, created_by: int
    ) -> QuizQuestion:
        q = QuizQuestion(
            id=str(uuid.uuid4()),
            question=question,
            options=options,
            correct_index=correct_index,
            created_by=created_by,
        )
        await self._quizzes.add(q)
        return q

    async def random_question(self) -> QuizQuestion | None:
        return await self._quizzes.random_question()

    async def answer(self, user_id: int, question_id: str, chosen_index: int) -> bool:
        """Javobni tekshiradi, to'g'ri bo'lsa XP+coin beradi. ``True``/``False``
        qaytaradi (to'g'ri javobmi).
        """

        question = await self._quizzes.get(question_id)
        if question is None:
            return False

        is_correct = chosen_index == question.correct_index
        if is_correct:
            profile = await self._economy.get(user_id)
            profile.xp += QUIZ_CORRECT_XP
            profile.coins += QUIZ_CORRECT_COINS
            profile.recompute_level()
            await self._economy.save(profile)
        return is_correct
