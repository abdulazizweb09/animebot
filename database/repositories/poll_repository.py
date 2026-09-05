"""``polls.json`` va ``quizzes.json`` repositorylari — #45, #46."""

from __future__ import annotations

from database.json_manager import JsonManager
from database.models.poll import Poll, QuizQuestion
from database.repositories.base_repository import BaseRepository


class PollRepository(BaseRepository[Poll]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "polls.json", Poll, id_field="id")

    async def active_polls(self) -> list[Poll]:
        polls = await self.all()
        return [p for p in polls if p.is_active]

    async def vote(self, poll_id: str, user_id: int, option_index: int) -> Poll | None:
        result_holder: dict[str, dict] = {}

        def _updater(data: list[dict]) -> list[dict]:
            for entry in data:
                if entry.get("id") == poll_id:
                    votes = entry.get("votes", {})
                    votes[str(user_id)] = option_index
                    entry["votes"] = votes
                    result_holder["poll"] = entry
                    return data
            result_holder["poll"] = None
            return data

        await self._manager.update(self._filename, _updater, default=[])
        raw = result_holder.get("poll")
        return Poll.from_dict(raw) if raw else None


class QuizRepository(BaseRepository[QuizQuestion]):
    def __init__(self, manager: JsonManager) -> None:
        super().__init__(manager, "quizzes.json", QuizQuestion, id_field="id")

    async def random_question(self):
        import random

        questions = await self.all()
        return random.choice(questions) if questions else None
