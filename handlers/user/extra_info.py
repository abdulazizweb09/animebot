"""ℹ️ Qo'shimcha — anime kartochkasidagi "Extra" bo'limi.

Bu handler avval hech qanday funksiyaga ulanmagan "ℹ️ Qo'shimcha"
tugmasini to'ldiradi. Bitta menyu orqali quyidagilarni ko'rsatadi:
    • #34 Filler List / #35 Canon List
    • #36 Opening/Ending List
    • #40 Character Gallery (+ #26 Voice Actor)
    • #41 Wallpaper Gallery
    • #42 Trailer Gallery
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from container import Container

router = Router(name="user_extra_info")


def _extra_menu_keyboard(anime_code: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🎞 Filler/Canon", callback_data=f"extrainfo:filler:{anime_code}"),
            InlineKeyboardButton(text="🎵 OP/ED", callback_data=f"extrainfo:opEd:{anime_code}"),
        ],
        [
            InlineKeyboardButton(text="🧑‍🎤 Personajlar", callback_data=f"extrainfo:chars:{anime_code}"),
        ],
        [
            InlineKeyboardButton(text="🖼 Wallpaper", callback_data=f"extrainfo:wall:{anime_code}"),
            InlineKeyboardButton(text="🎬 Treylerlar", callback_data=f"extrainfo:trailer:{anime_code}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("extra:"))
async def show_extra_menu(callback: CallbackQuery) -> None:
    anime_code = callback.data.split(":", 1)[1]
    await callback.message.answer(
        "ℹ️ Qo'shimcha ma'lumot:", reply_markup=_extra_menu_keyboard(anime_code)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("extrainfo:filler:"))
async def show_filler_canon(callback: CallbackQuery, container: Container) -> None:
    anime_code = callback.data.split(":", 2)[2]
    filler = await container.anime_service.filler_episodes(anime_code)
    canon = await container.anime_service.canon_episodes(anime_code)

    lines = ["🎞 <b>Filler / Canon</b>\n"]
    if canon:
        lines.append("✅ Canon: " + ", ".join(str(e.number) for e in canon))
    if filler:
        lines.append("⏭ Filler (o'tkazib yuborsa bo'ladi): " + ", ".join(str(e.number) for e in filler))
    if not filler and not canon:
        lines.append("Hozircha belgilanmagan.")

    await callback.message.answer("\n".join(lines))
    await callback.answer()


@router.callback_query(F.data.startswith("extrainfo:opEd:"))
async def show_op_ed(callback: CallbackQuery, container: Container) -> None:
    anime_code = callback.data.split(":", 2)[2]
    anime = await container.anime_service.get_detail(anime_code)
    if anime is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    lines = ["🎵 <b>Opening / Ending</b>\n"]
    if anime.op_songs:
        lines.append("🎶 Opening: " + ", ".join(anime.op_songs))
    if anime.ed_songs:
        lines.append("🎶 Ending: " + ", ".join(anime.ed_songs))
    if not anime.op_songs and not anime.ed_songs:
        lines.append("Hozircha qo'shilmagan.")

    await callback.message.answer("\n".join(lines))
    await callback.answer()


@router.callback_query(F.data.startswith("extrainfo:chars:"))
async def show_characters(callback: CallbackQuery, container: Container) -> None:
    anime_code = callback.data.split(":", 2)[2]
    characters = await container.character_service.list_for_anime(anime_code)

    if not characters:
        await callback.message.answer("🧑‍🎤 Personajlar hozircha qo'shilmagan.")
        await callback.answer()
        return

    for c in characters[:10]:
        va_part = f"\n🎙 Ovoz beruvchi: {c.voice_actor}" if c.voice_actor else ""
        caption = f"🧑‍🎤 <b>{c.name}</b>{va_part}"
        if c.description:
            caption += f"\n\n{c.description}"

        if c.image_file_id:
            await callback.message.answer_photo(c.image_file_id, caption=caption)
        else:
            await callback.message.answer(caption)

    await callback.answer()


@router.callback_query(F.data.startswith("extrainfo:wall:"))
async def show_wallpapers(callback: CallbackQuery, container: Container) -> None:
    anime_code = callback.data.split(":", 2)[2]
    wallpapers = await container.character_service.wallpapers(anime_code)

    if not wallpapers:
        await callback.message.answer("🖼 Wallpaperlar hozircha qo'shilmagan.")
        await callback.answer()
        return

    for w in wallpapers[:10]:
        await callback.message.answer_photo(w.file_id)
    await callback.answer()


@router.callback_query(F.data.startswith("extrainfo:trailer:"))
async def show_trailers(callback: CallbackQuery, container: Container) -> None:
    anime_code = callback.data.split(":", 2)[2]
    trailers = await container.character_service.trailers(anime_code)

    if not trailers:
        await callback.message.answer("🎬 Treylerlar hozircha qo'shilmagan.")
        await callback.answer()
        return

    for tr in trailers[:5]:
        await callback.message.answer_video(tr.file_id, caption="🎬 Treyler")
    await callback.answer()
