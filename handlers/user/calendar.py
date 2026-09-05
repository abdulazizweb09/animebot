"""📅 Anime Calendar — #20."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_calendar")


@router.message(F.text.in_(all_variants("btn_calendar")))
async def show_calendar(message: Message, container: Container, db_user: User) -> None:
    today = await container.schedule_service.today_releases()

    lines = []
    if today:
        lines.append(t("calendar_today_title", db_user.language))
        for entry, anime in today:
            title = anime.title_uz if anime else entry.anime_code
            time_str = entry.release_datetime().strftime("%H:%M")
            lines.append(f"  • {title} — {entry.episode_number}-qism ({time_str} UTC)")
    else:
        lines.append(t("calendar_today_empty", db_user.language))

    lines.append("")

    upcoming = await container.schedule_service.upcoming_releases(days=7)
    if upcoming:
        lines.append(t("calendar_upcoming_title", db_user.language))
        for entry, anime in upcoming:
            title = anime.title_uz if anime else entry.anime_code
            date_str = entry.release_datetime().strftime("%m-%d %H:%M")
            lines.append(f"  • {title} — {entry.episode_number}-qism ({date_str} UTC)")
    else:
        lines.append(t("calendar_upcoming_empty", db_user.language))

    await message.answer("\n".join(lines))
