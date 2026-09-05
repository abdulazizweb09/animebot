"""Foydalanuvchi tomonidagi FSM state guruhlari."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    waiting_query = State()


class AIChatStates(StatesGroup):
    chatting = State()


class VipStates(StatesGroup):
    waiting_receipt = State()


class FilterStates(StatesGroup):
    waiting_genre = State()
    waiting_year = State()
    waiting_studio = State()
    waiting_min_rating = State()


class CompareStates(StatesGroup):
    waiting_first_code = State()
    waiting_second_code = State()


class PromoStates(StatesGroup):
    waiting_code = State()


class CharacterSearchStates(StatesGroup):
    waiting_query = State()


class CommentStates(StatesGroup):
    waiting_text = State()


class AnimeRequestStates(StatesGroup):
    waiting_title = State()


class BugReportStates(StatesGroup):
    waiting_text = State()


class ManualProgressStates(StatesGroup):
    waiting_episode_number = State()
