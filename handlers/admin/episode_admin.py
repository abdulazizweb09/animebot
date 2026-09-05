"""📼 Epizod va video qo'shish (admin).

Ikki rejim mavjud:
    1. **Bitta qism** — bitta epizod uchun bir nechta sifatda video yuklash
       (480p/720p/1080p) — filmlar yoki alohida qismlarni to'ldirish uchun.
    2. **Ko'p qism (bulk)** — bir nechta video ketma-ket yuborilsa, HAR BIR
       video AVTOMATIK RAVISHDA alohida qism (episode) sifatida qo'shiladi
       (masalan, 100 ta video yuborilsa — 100 ta qism yaratiladi, raqamlari
       ketma-ket avtomatik beriladi). Bu rejim serial animening barcha
       qismlarini bir yo'la yuklash uchun mo'ljallangan.

Eslatma: bu handler faqat adminlar uchun ochiq bo'lgani sabab,
``FloodMiddleware`` va ``ThrottlingMiddleware`` adminlarni tekshirishdan
istisno qiladi — aks holda ko'p video ketma-ket yuborilganda ular
"flood" deb noto'g'ri bloklanib, video/qismlar jimgina yo'qolib qolardi.
"""

from __future__ import annotations

import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.enums import LogAction, Permission
from container import Container
from database.models.anime import Episode, Video
from filters.admin_filters import IsAdmin
from keyboards.admin.quality_select import quality_select_keyboard
from states.admin_states import EpisodeStates
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="admin_episode")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _notify_new_episode(
    bot: Bot, container: Container, anime_code: str, episode_number: int
) -> None:
    """Anime'ni sevimli yoki ro'yxatiga qo'shgan foydalanuvchilarga yangi
    qism chiqqani haqida xabar beradi (yangi funksiya — oldin faqat
    JADVAL asosidagi eslatma bor edi, endi haqiqiy yuklash lahzasida ham
    xabar beriladi).
    """

    anime = await container.animes.get_by_code(anime_code)
    title = anime.title_uz if anime else anime_code

    favorites = await container.favorites.find_all(lambda f: f.get("anime_code") == anime_code)
    watchers = await container.watchlist.find_all(lambda w: w.get("anime_code") == anime_code)
    user_ids = {f.user_id for f in favorites if not f.is_deleted} | {
        w.user_id for w in watchers if not w.is_deleted
    }

    for user_id in user_ids:
        await container.notification_service.create_and_send(
            bot,
            user_id,
            kind="new_episode",
            title="🆕 Yangi qism chiqdi!",
            text=f"{title} — {episode_number}-qism endi mavjud!",
            anime_code=anime_code,
        )

_MODE_SINGLE = "epmode:single"
_MODE_BULK = "epmode:bulk"


def _mode_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="1️⃣ Bitta qism (bir nechta sifat)", callback_data=_MODE_SINGLE)],
        [
            InlineKeyboardButton(
                text="📦 Ko'p qism (har video = alohida qism)", callback_data=_MODE_BULK
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "📼 Video qo'shish")
async def start_add_episode(message: Message, state: FSMContext, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.VIDEO_ADD
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return
    await state.set_state(EpisodeStates.waiting_anime_code)
    await message.answer("🎬 Anime kodini kiriting:")


@router.message(EpisodeStates.waiting_anime_code, F.text)
async def anime_code_for_episode(message: Message, state: FSMContext, container: Container) -> None:
    code = message.text.strip().upper()
    anime = await container.animes.get_by_code(code)
    if anime is None:
        await message.answer("❌ Bunday kod topilmadi. Qaytadan kiriting:")
        return

    await state.update_data(anime_code=code)
    await state.set_state(EpisodeStates.waiting_mode)
    await message.answer(
        "📼 Yuklash rejimini tanlang:", reply_markup=_mode_keyboard()
    )


# ---------------------------------------------------------------------------
# Rejim 1: Bitta qism, bir nechta sifat
# ---------------------------------------------------------------------------


@router.callback_query(EpisodeStates.waiting_mode, F.data == _MODE_SINGLE)
async def choose_single_mode(
    callback: CallbackQuery, state: FSMContext, container: Container, bot: Bot
) -> None:
    data = await state.get_data()
    anime_code = data["anime_code"]

    episode = await container.episodes.add_with_auto_number(
        anime_code,
        lambda n: Episode(id=str(uuid.uuid4()), anime_code=anime_code, number=n),
    )
    await container.audit_service.log(
        callback.from_user.id,
        LogAction.EPISODE_CREATE,
        {"anime_code": anime_code, "episode_number": episode.number},
    )
    await _notify_new_episode(bot, container, anime_code, episode.number)

    await state.update_data(episode_id=episode.id, video_queue=[])
    await state.set_state(EpisodeStates.waiting_video)
    await callback.message.answer(
        f"✅ {episode.number}-qism yaratildi.\n📼 Endi video faylni yuboring "
        f"(bir nechta sifatda yuborsangiz bo'ladi). Tugatish uchun /done"
    )
    await callback.answer()


@router.message(EpisodeStates.waiting_video, F.video)
async def video_received(message: Message, state: FSMContext) -> None:
    """Har bir kelgan videoni navbatga (queue) qo'shadi — bir nechta video
    ketma-ket, sifat tanlanishidan oldin kelsa ham, hech biri yo'qolmaydi
    (avvalgi versiyada bitta ``pending_file_id`` ustiga yozilib, tez-tez
    yuborilgan videolar bir-birini bosib ketardi — shu xato tuzatildi).
    """

    data = await state.get_data()
    queue: list[str] = data.get("video_queue", [])
    queue.append(message.video.file_id)
    await state.update_data(video_queue=queue)

    if len(queue) == 1:
        await message.answer(
            "📺 Bu videoning sifatini tanlang:", reply_markup=quality_select_keyboard()
        )
    else:
        await message.answer(
            f"📥 Navbatga qo'shildi ({len(queue)}-video). Avval oldingi video uchun "
            f"sifatni tanlang, keyin navbatdagilar so'raladi."
        )


@router.callback_query(EpisodeStates.waiting_video, F.data.startswith("upl_q:"))
async def video_quality_chosen(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    quality = callback.data.split(":", 1)[1]
    data = await state.get_data()
    queue: list[str] = data.get("video_queue", [])
    episode_id = data.get("episode_id")
    anime_code = data.get("anime_code")

    if not queue or not episode_id:
        await callback.answer("Xatolik: video topilmadi.", show_alert=True)
        return

    file_id = queue.pop(0)
    video = Video(
        id=str(uuid.uuid4()),
        episode_id=episode_id,
        anime_code=anime_code,
        file_id=file_id,
        quality=quality,
        uploaded_by=callback.from_user.id,
    )
    await container.videos.add(video)
    await container.audit_service.log(
        callback.from_user.id, LogAction.VIDEO_ADD, {"episode_id": episode_id, "quality": quality}
    )

    await state.update_data(video_queue=queue)

    if queue:
        await callback.message.answer(
            f"✅ {quality} saqlandi. Navbatda yana {len(queue)} ta video bor — "
            f"keyingisi uchun sifatni tanlang:",
            reply_markup=quality_select_keyboard(),
        )
    else:
        await callback.message.answer(
            f"✅ {quality} video saqlandi. Yana video yuboring yoki /done bilan tugating."
        )
    await callback.answer()


@router.message(EpisodeStates.waiting_video, F.text == "/done")
async def finish_single_upload(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("✅ Yuklash yakunlandi.")


# ---------------------------------------------------------------------------
# Rejim 2: Ko'p qism (bulk) — har video = alohida qism
# ---------------------------------------------------------------------------


@router.callback_query(EpisodeStates.waiting_mode, F.data == _MODE_BULK)
async def choose_bulk_mode(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(bulk_quality=None, bulk_count=0)
    await callback.message.answer(
        "📦 Bulk rejim: barcha yuboriladigan videolar qanday sifatda saqlansin?",
        reply_markup=quality_select_keyboard(),
    )
    await callback.answer()


@router.callback_query(EpisodeStates.waiting_mode, F.data.startswith("upl_q:"))
async def bulk_quality_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    quality = callback.data.split(":", 1)[1]
    await state.update_data(bulk_quality=quality, bulk_count=0)
    await state.set_state(EpisodeStates.bulk_uploading)
    await callback.message.answer(
        f"📦 Sifat: {quality}. Endi videolarni ketma-ket yuboring — "
        f"HAR BIR video avtomatik alohida qism sifatida qo'shiladi "
        f"(masalan, 100 ta video = 100 ta qism). Tugatganda /done bosing."
    )
    await callback.answer()


@router.message(EpisodeStates.bulk_uploading, F.video)
async def bulk_video_received(message: Message, state: FSMContext, container: Container) -> None:
    """Har bir kelgan video darhol YANGI qism sifatida qo'shiladi — hech
    qanday qo'shimcha tasdiqlash so'ralmaydi, shuning uchun 100 ta video
    ketma-ket yuborilsa, 100 ta qism ketma-ket raqamlanib yaratiladi.
    """

    data = await state.get_data()
    anime_code = data["anime_code"]
    quality = data.get("bulk_quality", "480p")

    episode = await container.episodes.add_with_auto_number(
        anime_code,
        lambda n: Episode(id=str(uuid.uuid4()), anime_code=anime_code, number=n),
    )

    video = Video(
        id=str(uuid.uuid4()),
        episode_id=episode.id,
        anime_code=anime_code,
        file_id=message.video.file_id,
        quality=quality,
        uploaded_by=message.from_user.id,
    )
    await container.videos.add(video)

    await container.audit_service.log(
        message.from_user.id,
        LogAction.EPISODE_CREATE,
        {"anime_code": anime_code, "episode_number": episode.number, "bulk": True},
    )

    new_count = data.get("bulk_count", 0) + 1
    await state.update_data(bulk_count=new_count)

    # Har bir video uchun alohida xabar yubormaymiz (100 ta video = 100 ta
    # xabar bo'lib, Telegram flood-limitiga urilishi mumkin). Buning o'rniga
    # har 10-videoda oraliq progress ko'rsatamiz, yakuniy hisobot /done da.
    if new_count % 10 == 0:
        await message.answer(f"📦 {new_count} ta qism qo'shildi...")


@router.message(EpisodeStates.bulk_uploading, F.text == "/done")
async def finish_bulk_upload(message: Message, state: FSMContext, container: Container, bot: Bot) -> None:
    data = await state.get_data()
    count = data.get("bulk_count", 0)
    anime_code = data.get("anime_code")
    await state.clear()
    await message.answer(
        f"✅ Bulk yuklash yakunlandi: <b>{anime_code}</b> uchun {count} ta yangi qism qo'shildi."
    )

    if count > 0 and anime_code:
        # Ko'p qism qo'shilganda har biriga alohida xabar yubormaymiz
        # (spam bo'lmasligi uchun) — bitta umumlashtirilgan xabar yetarli.
        anime = await container.animes.get_by_code(anime_code)
        title = anime.title_uz if anime else anime_code

        favorites = await container.favorites.find_all(lambda f: f.get("anime_code") == anime_code)
        watchers = await container.watchlist.find_all(lambda w: w.get("anime_code") == anime_code)
        user_ids = {f.user_id for f in favorites if not f.is_deleted} | {
            w.user_id for w in watchers if not w.is_deleted
        }
        for user_id in user_ids:
            await container.notification_service.create_and_send(
                bot,
                user_id,
                kind="new_episode",
                title="🆕 Yangi qismlar chiqdi!",
                text=f"{title} — {count} ta yangi qism qo'shildi!",
                anime_code=anime_code,
            )
