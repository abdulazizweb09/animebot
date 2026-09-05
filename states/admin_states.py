"""Admin panel uchun FSM state guruhlari."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class VipReviewStates(StatesGroup):
    waiting_reject_reason = State()


class AnimeStates(StatesGroup):
    waiting_code = State()
    waiting_title = State()
    waiting_description = State()
    waiting_poster = State()
    waiting_genres = State()
    waiting_studio = State()
    waiting_type = State()
    waiting_year = State()
    confirm = State()


class EpisodeStates(StatesGroup):
    waiting_anime_code = State()
    waiting_mode = State()
    waiting_video = State()
    bulk_uploading = State()


class BroadcastStates(StatesGroup):
    waiting_content = State()
    waiting_audience = State()
    waiting_genre = State()
    confirm = State()


class AdminManageStates(StatesGroup):
    waiting_new_admin_id = State()
    waiting_permission_selection = State()


class BanStates(StatesGroup):
    waiting_user_id = State()
    waiting_reason = State()


class DeleteAnimeStates(StatesGroup):
    waiting_code = State()


class SubscriptionStates(StatesGroup):
    waiting_channel_id = State()
    waiting_channel_title = State()
    waiting_channel_link = State()


class CollectionStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_poster = State()
    waiting_anime_codes = State()


class PromoCreateStates(StatesGroup):
    waiting_type = State()
    waiting_value = State()
    waiting_max_uses = State()
    waiting_expiry_days = State()


class GiftVipStates(StatesGroup):
    waiting_user_id = State()
    waiting_days = State()


class ScheduleStates(StatesGroup):
    waiting_anime_code = State()
    waiting_episode_number = State()
    waiting_datetime = State()
