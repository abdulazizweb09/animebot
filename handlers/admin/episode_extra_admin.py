"""Filler/Canon belgilash va Opening/Ending qo'shish (#34, #35, #36) — admin."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin

router = Router(name="admin_episode_extra")
router.message.filter(IsAdmin())


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.ANIME_EDIT
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


@router.message(F.text.startswith("/setfiller "))
async def set_filler(message: Message, container: Container) -> None:
    """Format: /setfiller <anime_kod> <qism_raqami>"""

    if not await _require_permission(message, container):
        return

    parts = message.text.split()
    if len(parts) != 3 or not parts[2].isdigit():
        await message.answer("⚠️ Format: /setfiller <anime_kod> <qism_raqami>")
        return

    anime_code, number = parts[1].upper(), int(parts[2])
    episode = await container.episodes.get_by_number(anime_code, number)
    if episode is None:
        await message.answer("❌ Bunday qism topilmadi.")
        return

    await container.episodes.update(episode.id, {"is_filler": not episode.is_filler})
    status = "filler" if not episode.is_filler else "canon"
    await message.answer(f"✅ {anime_code} {number}-qism endi: {status}")


@router.message(F.text.startswith("/addop "))
async def add_opening(message: Message, container: Container) -> None:
    """Format: /addop <anime_kod> <qo'shiq nomi>"""

    if not await _require_permission(message, container):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("⚠️ Format: /addop <anime_kod> <qo'shiq nomi>")
        return

    anime_code, song = parts[1].upper(), parts[2]
    anime = await container.animes.get_by_code(anime_code)
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return

    await container.animes.edit(anime_code, {"op_songs": anime.op_songs + [song]})
    await message.answer(f"✅ Opening qo'shildi: {song}")


@router.message(F.text.startswith("/added "))
async def add_ending(message: Message, container: Container) -> None:
    """Format: /added <anime_kod> <qo'shiq nomi>"""

    if not await _require_permission(message, container):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("⚠️ Format: /added <anime_kod> <qo'shiq nomi>")
        return

    anime_code, song = parts[1].upper(), parts[2]
    anime = await container.animes.get_by_code(anime_code)
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return

    await container.animes.edit(anime_code, {"ed_songs": anime.ed_songs + [song]})
    await message.answer(f"✅ Ending qo'shildi: {song}")


@router.message(F.text.startswith("/setwatchorder "))
async def set_watch_order(message: Message, container: Container) -> None:
    """Format: /setwatchorder <anime_kod> <raqam> — #32 Watch Order, #33 Manga Order."""

    if not await _require_permission(message, container):
        return

    parts = message.text.split()
    if len(parts) != 3 or not parts[2].isdigit():
        await message.answer("⚠️ Format: /setwatchorder <anime_kod> <raqam>")
        return

    anime_code, order = parts[1].upper(), int(parts[2])
    success = await container.collection_service.set_watch_order(anime_code, order)
    if success:
        await message.answer(f"✅ {anime_code} uchun tomosha tartibi: {order}")
    else:
        await message.answer("❌ Bunday anime topilmadi.")


@router.message(F.text.startswith("/addalias "))
async def add_alias(message: Message, container: Container) -> None:
    """Format: /addalias <anime_kod> <muqobil_nom>

    Qidiruv sifatini oshiradi — masalan "AOT" kodli animega "Attack on
    Titan", "Shingeki no Kyojin" kabi muqobil nomlar qo'shilsa, foydalanuvchi
    ularning istalgani bo'yicha ham topa oladi.
    """

    if not await _require_permission(message, container):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        await message.answer("⚠️ Format: /addalias <anime_kod> <muqobil_nom>")
        return

    anime_code, alias = parts[1].upper(), parts[2]
    anime = await container.animes.get_by_code(anime_code)
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return

    await container.aliases.add_alias(anime_code, alias)
    await message.answer(f"✅ '{alias}' {anime_code} uchun muqobil nom sifatida qo'shildi.")
