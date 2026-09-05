"""Character/Gallery/News/Announcements qo'shish (admin) — #25, #26, #40-44."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin

router = Router(name="admin_content")
router.message.filter(IsAdmin())


class MediaUploadStates(StatesGroup):
    waiting_wallpaper = State()
    waiting_trailer = State()


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.CONTENT_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


# ---------------------------------------------------------------------------
# #25, #26 — Character qo'shish
# ---------------------------------------------------------------------------


@router.message(F.text.startswith("/addcharacter "))
async def add_character(message: Message, container: Container) -> None:
    """Format: /addcharacter <anime_kod> | <ism> | <ovoz_aktyori_yoki_->"""

    if not await _require_permission(message, container):
        return

    body = message.text[len("/addcharacter "):]
    parts = [p.strip() for p in body.split("|")]
    if len(parts) != 3:
        await message.answer(
            "⚠️ Format: /addcharacter <anime_kod> | <ism> | <ovoz_aktyori_yoki_->"
        )
        return

    anime_code, name, voice_actor_raw = parts
    anime = await container.animes.get_by_code(anime_code.upper())
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return

    voice_actor = None if voice_actor_raw == "-" else voice_actor_raw
    character = await container.character_service.add_character(
        anime_code.upper(), name, voice_actor, None
    )
    await message.answer(f"✅ Personaj qo'shildi: {character.name}")


# ---------------------------------------------------------------------------
# #41 Wallpaper, #42 Trailer
# ---------------------------------------------------------------------------


@router.message(F.text.startswith("/addwallpaper "))
async def start_wallpaper(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    code = message.text.split(" ", 1)[1].strip().upper()
    anime = await container.animes.get_by_code(code)
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return
    await state.update_data(media_anime_code=code)
    await state.set_state(MediaUploadStates.waiting_wallpaper)
    await message.answer("🖼 Wallpaper rasmini yuboring:")


@router.message(MediaUploadStates.waiting_wallpaper, F.photo)
async def receive_wallpaper(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    await state.clear()
    await container.character_service.add_media(
        data["media_anime_code"], "wallpaper", message.photo[-1].file_id
    )
    await message.answer("✅ Wallpaper qo'shildi.")


@router.message(F.text.startswith("/addtrailer "))
async def start_trailer(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    code = message.text.split(" ", 1)[1].strip().upper()
    anime = await container.animes.get_by_code(code)
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return
    await state.update_data(media_anime_code=code)
    await state.set_state(MediaUploadStates.waiting_trailer)
    await message.answer("🎬 Treyler videosini yuboring:")


@router.message(MediaUploadStates.waiting_trailer, F.video)
async def receive_trailer(message: Message, state: FSMContext, container: Container) -> None:
    data = await state.get_data()
    await state.clear()
    await container.character_service.add_media(
        data["media_anime_code"], "trailer", message.video.file_id
    )
    await message.answer("✅ Treyler qo'shildi.")


# ---------------------------------------------------------------------------
# #43 News, #44 Announcements
# ---------------------------------------------------------------------------


@router.message(F.text.startswith("/publishnews "))
async def publish_news(message: Message, container: Container) -> None:
    """Format: /publishnews <sarlavha> | <matn>"""

    if not await _require_permission(message, container):
        return

    body = message.text[len("/publishnews "):]
    parts = [p.strip() for p in body.split("|", 1)]
    if len(parts) != 2:
        await message.answer("⚠️ Format: /publishnews <sarlavha> | <matn>")
        return

    title, content = parts
    await container.news_service.publish(title, content, kind="news", created_by=message.from_user.id)
    await message.answer("✅ Yangilik e'lon qilindi.")


@router.message(F.text.startswith("/publishannounce "))
async def publish_announcement(message: Message, container: Container) -> None:
    """Format: /publishannounce <sarlavha> | <matn>"""

    if not await _require_permission(message, container):
        return

    body = message.text[len("/publishannounce "):]
    parts = [p.strip() for p in body.split("|", 1)]
    if len(parts) != 2:
        await message.answer("⚠️ Format: /publishannounce <sarlavha> | <matn>")
        return

    title, content = parts
    await container.news_service.publish(
        title, content, kind="announcement", created_by=message.from_user.id
    )
    await message.answer("✅ E'lon joylandi.")
