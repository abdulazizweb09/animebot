"""🎞 Anime Collection / Franchise boshqaruvi (admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin
from states.admin_states import CollectionStates

router = Router(name="admin_collection")
router.message.filter(IsAdmin())


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.COLLECTION_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


@router.message(F.text == "🎞 Kolleksiyalar")
async def collection_menu(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    collections = await container.collection_service.list_all()
    lines = ["🎞 Mavjud kolleksiyalar:"] if collections else ["🎞 Hozircha kolleksiya yo'q."]
    for c in collections:
        if c.is_deleted:
            continue
        animes = await container.collection_service.get_animes(c.id)
        lines.append(f"• {c.title} — {len(animes)} ta anime (ID: <code>{c.id}</code>)")

    lines.append(
        "\n➕ Yangi kolleksiya yaratish uchun: /newcollection"
        "\n🔗 Animeni kolleksiyaga bog'lash uchun: /attach [collection_id] [anime_kod]"
    )
    await message.answer("\n".join(lines))


@router.message(F.text == "/newcollection")
async def start_new_collection(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container):
        return
    await state.set_state(CollectionStates.waiting_title)
    await message.answer("🎞 Kolleksiya nomini kiriting (masalan: Naruto Collection):")


@router.message(CollectionStates.waiting_title, F.text)
async def collection_title_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(CollectionStates.waiting_description)
    await message.answer("📄 Tavsif kiriting (yoki /skip):")


@router.message(CollectionStates.waiting_description, F.text == "/skip")
async def collection_description_skipped(message: Message, state: FSMContext) -> None:
    await state.update_data(description="")
    await state.set_state(CollectionStates.waiting_poster)
    await message.answer("🖼 Poster yuboring (yoki /skip):")


@router.message(CollectionStates.waiting_description, F.text)
async def collection_description_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(CollectionStates.waiting_poster)
    await message.answer("🖼 Poster yuboring (yoki /skip):")


@router.message(CollectionStates.waiting_poster, F.text == "/skip")
async def collection_poster_skipped(message: Message, state: FSMContext, container: Container) -> None:
    await _finish_collection(message, state, container, poster_file_id=None)


@router.message(CollectionStates.waiting_poster, F.photo)
async def collection_poster_entered(message: Message, state: FSMContext, container: Container) -> None:
    await _finish_collection(message, state, container, poster_file_id=message.photo[-1].file_id)


async def _finish_collection(
    message: Message, state: FSMContext, container: Container, poster_file_id: str | None
) -> None:
    data = await state.get_data()
    await state.clear()

    collection = await container.collection_service.create(
        title=data["title"],
        description=data.get("description", ""),
        created_by=message.from_user.id,
        poster_file_id=poster_file_id,
    )
    await message.answer(
        f"✅ Kolleksiya yaratildi: <b>{collection.title}</b>\n"
        f"ID: <code>{collection.id}</code>\n\n"
        f"Endi animelarni bog'lash uchun: /attach {collection.id} [anime_kod]"
    )


@router.message(F.text.startswith("/attach "))
async def attach_anime_to_collection(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    parts = message.text.split(" ")
    if len(parts) != 3:
        await message.answer("⚠️ Format: /attach [collection_id] [anime_kod]")
        return

    _, collection_id, anime_code = parts
    success = await container.collection_service.attach_anime(collection_id, anime_code.upper())
    if success:
        await message.answer(f"✅ {anime_code.upper()} kolleksiyaga bog'landi.")
    else:
        await message.answer("❌ Kolleksiya yoki anime topilmadi.")


@router.message(F.text.startswith("/detach "))
async def detach_anime_from_collection(message: Message, container: Container) -> None:
    """Format: /detach <anime_kod> — animeni kolleksiyadan chiqaradi."""

    if not await _require_permission(message, container):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: /detach <anime_kod>")
        return

    anime_code = parts[1].upper()
    anime = await container.animes.get_by_code(anime_code)
    if anime is None:
        await message.answer("❌ Bunday anime topilmadi.")
        return

    await container.collection_service.detach_anime(anime_code)
    await message.answer(f"✅ {anime_code} kolleksiyadan chiqarildi.")
