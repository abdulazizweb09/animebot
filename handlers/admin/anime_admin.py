"""🎬 Anime qo'shish / o'chirish / trash boshqaruvi (admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.enums import LogAction, Permission
from container import Container
from filters.admin_filters import IsAdmin
from states.admin_states import AnimeStates, DeleteAnimeStates

router = Router(name="admin_anime")
router.message.filter(IsAdmin())


async def _require_permission(message: Message, container: Container, permission: Permission) -> bool:
    allowed = await container.permission_service.has_permission(message.from_user.id, permission)
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


# ---------------------------------------------------------------------------
# Anime qo'shish (FSM)
# ---------------------------------------------------------------------------


@router.message(F.text == "🎬 Anime qo'shish")
async def start_add_anime(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container, Permission.ANIME_ADD):
        return
    await state.set_state(AnimeStates.waiting_code)
    await message.answer(
        "🎬 Anime uchun noyob KOD kiriting (masalan: AOT-001).\nBekor qilish uchun /cancel"
    )


@router.message(AnimeStates.waiting_code, F.text)
async def anime_code_entered(message: Message, state: FSMContext, container: Container) -> None:
    code = message.text.strip().upper()
    if await container.animes.code_exists(code):
        await message.answer("⚠️ Bu kod band. Boshqa kod kiriting:")
        return
    await state.update_data(code=code)
    await state.set_state(AnimeStates.waiting_title)
    await message.answer("📝 Anime nomini kiriting:")


@router.message(AnimeStates.waiting_title, F.text)
async def anime_title_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(title_uz=message.text.strip())
    await state.set_state(AnimeStates.waiting_description)
    await message.answer("📄 Tavsif kiriting (yoki /skip):")


@router.message(AnimeStates.waiting_description, F.text == "/skip")
async def anime_description_skipped(message: Message, state: FSMContext) -> None:
    await state.update_data(description="")
    await state.set_state(AnimeStates.waiting_poster)
    await message.answer("🖼 Poster rasmini yuboring (yoki /skip):")


@router.message(AnimeStates.waiting_description, F.text)
async def anime_description_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(AnimeStates.waiting_poster)
    await message.answer("🖼 Poster rasmini yuboring (yoki /skip):")


@router.message(AnimeStates.waiting_poster, F.text == "/skip")
async def anime_poster_skipped(message: Message, state: FSMContext) -> None:
    await state.update_data(poster_file_id=None)
    await state.set_state(AnimeStates.waiting_genres)
    await message.answer("🏷 Janrlarni vergul bilan kiriting (masalan: Action, Drama):")


@router.message(AnimeStates.waiting_poster, F.photo)
async def anime_poster_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(poster_file_id=message.photo[-1].file_id)
    await state.set_state(AnimeStates.waiting_genres)
    await message.answer("🏷 Janrlarni vergul bilan kiriting (masalan: Action, Drama):")


@router.message(AnimeStates.waiting_genres, F.text)
async def anime_genres_entered(message: Message, state: FSMContext) -> None:
    genres = [g.strip() for g in message.text.split(",") if g.strip()]
    await state.update_data(genres=genres)
    await state.set_state(AnimeStates.waiting_studio)
    await message.answer("🎬 Studiya nomini kiriting (yoki /skip):")


@router.message(AnimeStates.waiting_studio, F.text == "/skip")
async def anime_studio_skipped(message: Message, state: FSMContext) -> None:
    await state.update_data(studio=None)
    await state.set_state(AnimeStates.waiting_type)
    await message.answer(
        "📼 Turini tanlang: tv / movie / ova / special (standart: tv)"
    )


@router.message(AnimeStates.waiting_studio, F.text)
async def anime_studio_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(studio=message.text.strip())
    await state.set_state(AnimeStates.waiting_type)
    await message.answer(
        "📼 Turini tanlang: tv / movie / ova / special (standart: tv)"
    )


@router.message(AnimeStates.waiting_type, F.text)
async def anime_type_entered(message: Message, state: FSMContext) -> None:
    from config.enums import AnimeType

    raw = message.text.strip().lower()
    anime_type = raw if raw in [t.value for t in AnimeType] else AnimeType.TV.value
    await state.update_data(anime_type=anime_type)
    await state.set_state(AnimeStates.waiting_year)
    await message.answer("📅 Chiqarilgan yilini kiriting (masalan: 2024):")


@router.message(AnimeStates.waiting_year, F.text)
async def anime_year_entered(
    message: Message, state: FSMContext, container: Container
) -> None:
    from database.models.anime import Anime

    year_text = message.text.strip()
    year = int(year_text) if year_text.isdigit() else None

    data = await state.get_data()
    await state.clear()

    anime = Anime(
        code=data["code"],
        title_uz=data["title_uz"],
        description=data.get("description", ""),
        poster_file_id=data.get("poster_file_id"),
        genres=data.get("genres", []),
        studio=data.get("studio"),
        anime_type=data.get("anime_type", "tv"),
        year=year,
        created_by=message.from_user.id,
    )
    _saved, added = await container.animes.add_if_absent(anime)
    if not added:
        await message.answer(
            f"⚠️ '{anime.code}' kodi orada boshqa admin tomonidan band qilindi. "
            f"Boshqa kod bilan qaytadan urinib ko'ring."
        )
        return

    await container.audit_service.log(
        message.from_user.id, LogAction.ANIME_CREATE, {"code": anime.code}
    )
    await message.answer(f"✅ Anime qo'shildi: <b>{anime.title_uz}</b> ({anime.code})")


@router.message(F.text == "/cancel")
async def cancel_fsm(message: Message, state: FSMContext) -> None:
    if await state.get_state() is not None:
        await state.clear()
        await message.answer("Bekor qilindi.")


# ---------------------------------------------------------------------------
# Anime o'chirish / Trash
# ---------------------------------------------------------------------------


@router.message(F.text == "🗑 Anime o'chirish")
async def start_delete_anime(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container, Permission.ANIME_DELETE):
        return
    await message.answer("🗑 O'chirmoqchi bo'lgan anime kodini kiriting:")
    await state.set_state(DeleteAnimeStates.waiting_code)


@router.message(DeleteAnimeStates.waiting_code, F.text)
async def finish_delete_anime(message: Message, state: FSMContext, container: Container) -> None:
    await state.clear()
    code = message.text.strip().upper()
    anime = await container.animes.get(code)
    if anime is None:
        await message.answer("❌ Bunday kod topilmadi.")
        return

    await container.animes.soft_delete(code)
    await container.audit_service.log(message.from_user.id, LogAction.ANIME_DELETE, {"code": code})
    await message.answer(
        f"🗑 O'chirildi (trash'ga ko'chirildi): {anime.title_uz} ({code})\n"
        f"Tiklash uchun: /restore {code}"
    )


@router.message(F.text == "♻️ Trash")
async def show_trash(message: Message, container: Container) -> None:
    if not await _require_permission(message, container, Permission.ANIME_DELETE):
        return
    all_items = await container.animes.all(include_deleted=True)
    deleted = [a for a in all_items if a.is_deleted]
    if not deleted:
        await message.answer("♻️ Trash bo'sh.")
        return
    lines = [f"• {a.code} — {a.title_uz}" for a in deleted[:30]]
    await message.answer(
        "♻️ O'chirilgan animelar (tiklash uchun admin bilan bog'laning yoki "
        "/restore [kod] buyrug'ini yuboring):\n\n" + "\n".join(lines)
    )


@router.message(F.text.startswith("/restore "))
async def restore_anime(message: Message, container: Container) -> None:
    if not await _require_permission(message, container, Permission.ANIME_DELETE):
        return
    code = message.text.split(" ", 1)[1].strip().upper()
    anime = await container.animes.get(code)
    if anime is None:
        await message.answer("Topilmadi.")
        return
    await container.animes.update(code, {"is_deleted": False})
    await container.audit_service.log(message.from_user.id, LogAction.ANIME_RESTORE, {"code": code})
    await message.answer(f"✅ Tiklandi: {code}")
