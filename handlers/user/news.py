"""📰 Anime News / Announcements (#43, #44)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from container import Container
from database.models.user import User
from utils.i18n import all_variants, t

router = Router(name="user_news")


@router.message(F.text.in_(all_variants("btn_news")))
async def show_news(message: Message, container: Container, db_user: User) -> None:
    news = await container.news_service.recent_news(limit=5)
    announcements = await container.news_service.recent_announcements(limit=5)
    combined = sorted(news + announcements, key=lambda n: n.created_at, reverse=True)

    if not combined:
        await message.answer(t("news_empty", db_user.language))
        return

    for post in combined[:10]:
        icon = "📢" if post.kind == "announcement" else "📰"
        text = f"{icon} <b>{post.title}</b>\n\n{post.content}"
        if post.image_file_id:
            await message.answer_photo(post.image_file_id, caption=text)
        else:
            await message.answer(text)
