"""Anime kartochkasi, epizodlar ro'yxati va video yuborish oqimi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import CONSTANTS
from config.enums import AnimeStatus
from container import Container
from database.models.user import User
from keyboards.user.anime_card import anime_card_keyboard
from keyboards.user.episodes import episode_list_keyboard, video_quality_keyboard

router = Router(name="user_anime_detail")

_STATUS_LABEL = {
    AnimeStatus.ONGOING.value: "🟢 Davom etmoqda",
    AnimeStatus.COMPLETED.value: "✅ Tugagan",
    AnimeStatus.ANNOUNCED.value: "📢 E'lon qilingan",
    AnimeStatus.PAUSED.value: "⏸ To'xtatilgan",
}


def _anime_caption(
    anime,
    progress_text: str | None = None,
    progress_percent: float | None = None,
    countdown_text: str | None = None,
) -> str:
    genres = ", ".join(anime.genres) if anime.genres else "—"
    rating = f"{anime.average_rating}/10 ({anime.rating_count} ta baho)" if anime.rating_count else "—"
    lines = [
        f"<b>{anime.title_uz}</b>",
        f"📅 Yil: {anime.year or '—'}",
        f"🏷 Janr: {genres}",
        f"📊 Holat: {_STATUS_LABEL.get(anime.status, anime.status)}",
        f"⭐️ Reyting: {rating}",
        f"👁 Ko'rishlar: {anime.views}",
    ]
    if progress_text:
        percent_part = f" ({progress_percent}%)" if progress_percent is not None else ""
        lines.append(f"📈 Progress: {progress_text} qism{percent_part}")
    if countdown_text:
        lines.append(f"⏳ {countdown_text}")
    if anime.is_vip_only:
        lines.append("💎 Faqat VIP foydalanuvchilar uchun")
    if anime.description:
        lines.append("")
        lines.append(anime.description)
    return "\n".join(lines)


async def send_anime_card(
    target, container: Container, db_user: User, anime, record_view: bool = True
) -> bool:
    """Anime kartochkasini (poster + caption + tugmalar) yuboradi.

    ``target`` — ``.answer()``/``.answer_photo()`` metodlariga ega har
    qanday obyekt (``Message`` yoki ``CallbackQuery.message``). Bir nechta
    joyda (anime kartochkasi ochilganda, ulashilgan havola orqali kirilganda,
    tasodifiy anime tanlanganda) TAKRORLANMASLIGI uchun markazlashtirilgan.

    VIP-only animeda ruxsat yo'q bo'lsa ``False`` qaytaradi va hech narsa
    yubormaydi (chaqiruvchi tomon foydalanuvchiga xabar berishi kerak).
    """

    if anime.is_vip_only:
        vip = await container.vips.get_active_for_user(db_user.user_id)
        if not vip and not db_user.is_admin:
            return False

    if record_view:
        await container.anime_service.view_anime(anime.code, user_id=db_user.user_id)

    is_fav = await container.favorites.is_favorite(db_user.user_id, anime.code)
    progress_text = await container.watchlist_service.progress_text(db_user.user_id, anime.code)
    progress_percent = await container.watchlist_service.progress_percent(db_user.user_id, anime.code)
    countdown_text = await container.schedule_service.countdown_text(anime.code)

    caption = _anime_caption(anime, progress_text, progress_percent, countdown_text)
    markup = anime_card_keyboard(anime, is_fav, db_user.language)

    if anime.poster_file_id:
        await target.answer_photo(anime.poster_file_id, caption=caption, reply_markup=markup)
    else:
        await target.answer(caption, reply_markup=markup)
    return True


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_ANIME}:"))
async def show_anime_card(callback: CallbackQuery, container: Container, db_user: User) -> None:
    code = callback.data.split(":", 1)[1]
    anime = await container.anime_service.get_detail(code)
    if anime is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    sent = await send_anime_card(callback.message, container, db_user, anime)
    if not sent:
        await callback.answer("💎 Bu anime faqat VIP foydalanuvchilar uchun.", show_alert=True)
        return
    await callback.answer()


@router.callback_query(F.data.startswith("share:"))
async def share_anime(callback: CallbackQuery, container: Container) -> None:
    anime_code = callback.data.split(":", 1)[1]
    anime = await container.anime_service.get_detail(anime_code)
    if anime is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    me = await callback.bot.get_me()
    link = f"https://t.me/{me.username}?start=anime_{anime_code}"
    await callback.message.answer(
        f"📤 <b>{anime.title_uz}</b> ni do'stlaringiz bilan ulashing:\n\n{link}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_EPISODE}:list:"))
async def show_episode_list(callback: CallbackQuery, container: Container) -> None:
    _, _, anime_code, page_raw = callback.data.split(":")
    page = int(page_raw)

    episodes = await container.anime_service.get_episodes(anime_code)
    if not episodes:
        await callback.answer("Epizodlar hali yuklanmagan.", show_alert=True)
        return

    await callback.message.answer(
        "🎬 Qismni tanlang:",
        reply_markup=episode_list_keyboard(anime_code, episodes, page=page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_PAGE}:eps:"))
async def paginate_episodes(callback: CallbackQuery, container: Container) -> None:
    parts = callback.data.split(":")
    anime_code = parts[2]
    page = int(parts[3])

    episodes = await container.anime_service.get_episodes(anime_code)
    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=episode_list_keyboard(anime_code, episodes, page=page)
        )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_EPISODE}:open:"))
async def show_video_qualities(callback: CallbackQuery, container: Container) -> None:
    episode_id = callback.data.split(":", 2)[2]
    videos = await container.anime_service.get_videos_for_episode(episode_id)
    if not videos:
        await callback.answer("Bu qism uchun video hali yuklanmagan.", show_alert=True)
        return

    await callback.message.answer(
        "📺 Sifatni tanlang:", reply_markup=video_quality_keyboard(episode_id, videos)
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_VIDEO}:"))
async def send_video(callback: CallbackQuery, container: Container, db_user: User) -> None:
    _, episode_id, quality = callback.data.split(":")
    video = await container.videos.get_by_quality(episode_id, quality)
    if video is None:
        await callback.answer("Video topilmadi.", show_alert=True)
        return

    episode = await container.episodes.get(episode_id)
    next_episode = None
    if episode:
        await container.history_service.record(db_user.user_id, episode.anime_code, episode_id)
        await container.watchlist_service.record_progress(
            db_user.user_id, episode.anime_code, episode.number
        )

        # Keyingi safar video so'ralganda sifatni qayta so'ramaslik uchun
        # foydalanuvchining oxirgi tanlagan sifatini eslab qolamiz.
        await container.users.update(db_user.user_id, {"preferred_quality": quality})

        # #48-50: har bir ko'rilgan epizod uchun XP/coin mukofoti
        profile = await container.economy_service.reward_episode_watched(db_user.user_id)

        # #12: 100/500/1000 epizod chegaralarini tekshirish va badge berish
        new_badges = await container.achievement_service.check_episode_milestones(
            db_user.user_id, profile.total_episodes_watched
        )
        for badge in new_badges:
            await callback.message.answer(
                f"🏆 Yangi yutuq: <b>{badge.label}</b>\n{badge.description}"
            )

        next_episode = await container.episodes.get_by_number(
            episode.anime_code, episode.number + 1
        )

    await container.videos.increment_downloads(video.id)

    buttons = [
        [
            InlineKeyboardButton(
                text="⚠️ Video buzilgan", callback_data=f"reportvideo:{video.id}"
            )
        ]
    ]
    if next_episode:
        next_videos = await container.videos.list_for_episode(next_episode.id)
        if next_videos:
            # Foydalanuvchi oldin tanlagan sifat mavjud bo'lsa o'shani,
            # bo'lmasa birinchi mavjud sifatni taklif qilamiz.
            preferred = next(
                (v for v in next_videos if v.quality == quality), next_videos[0]
            )
            buttons.insert(
                0,
                [
                    InlineKeyboardButton(
                        text=f"▶️ Keyingi qism ({next_episode.number})",
                        callback_data=f"{CONSTANTS.CB_VIDEO}:{next_episode.id}:{preferred.quality}",
                    )
                ],
            )

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer_video(video.file_id, caption=f"▶️ {quality}", reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("reportvideo:"))
async def report_broken_video(callback: CallbackQuery, container: Container, db_user: User) -> None:
    """⚠️ Video buzilgan — kontekstli xato xabari.

    Umumiy "🐛 Muammo haqida xabar berish" (Sozlamalar) dan farqli
    o'laroq, bu tugma qaysi anime/epizod/sifat ekanini AVTOMATIK biladi —
    foydalanuvchi hech narsa yozmasdan, bitta bosish bilan xabar beradi.
    """

    video_id = callback.data.split(":", 1)[1]
    video = await container.videos.get(video_id)
    if video is None:
        await callback.answer("Topilmadi", show_alert=True)
        return

    episode = await container.episodes.get(video.episode_id)
    anime = await container.animes.get_by_code(video.anime_code)
    episode_label = f"{episode.number}-qism" if episode else "?"
    anime_title = anime.title_uz if anime else video.anime_code

    await container.bug_report_service.submit(
        db_user.user_id,
        text=f"Avtomatik xabar: '{anime_title}' — {episode_label} ({video.quality}) ishlamayapti.",
        anime_code=video.anime_code,
    )
    await callback.answer("⚠️ Xabaringiz qabul qilindi. Tez orada tekshiramiz!", show_alert=True)
