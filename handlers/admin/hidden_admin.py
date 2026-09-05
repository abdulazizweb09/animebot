"""🕵️ Hidden Admin Menu (#54) + #60 Interactive Admin Dashboard.

Faqat MAIN-ADMIN uchun ochiq. ``/devtools`` yoki ``/dashboard`` buyrug'i
orqali kiriladi, ichkarida tugmalar orqali navigatsiya qilinadi — buyruq
yodlash shart emas.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from container import Container
from filters.admin_filters import IsMainAdmin
from keyboards.admin.dashboard import dashboard_back_keyboard, dashboard_keyboard

router = Router(name="admin_hidden")
router.message.filter(IsMainAdmin())
router.callback_query.filter(IsMainAdmin())


async def _build_health_text(container: Container) -> str:
    snapshot = await container.health_service.snapshot()
    uptime = container.health_service.format_uptime(snapshot["uptime_seconds"])
    return (
        "📊 <b>Health Dashboard</b>\n\n"
        f"⏱ Uptime: {uptime}\n\n"
        f"👥 Userlar: {snapshot['users_count']}\n"
        f"🎬 Animelar: {snapshot['animes_count']}\n"
        f"🎞 Epizodlar: {snapshot['episodes_count']}\n"
        f"📼 Videolar: {snapshot['videos_count']}\n\n"
        f"👁 Ko'rishlar (24s): {snapshot['anime_views_last_24h']}\n"
        f"🔍 Qidiruvlar (24s): {snapshot['searches_last_24h']}\n"
        f"🤖 AI so'rovlar (24s): {snapshot['ai_requests_last_24h']}\n"
        f"💎 VIP so'rovlar (24s): {snapshot['vip_requests_last_24h']}\n"
        f"🎟 Promo ishlatildi (24s): {snapshot['promo_redeems_last_24h']}\n"
        f"🧠 Quiz javoblar (24s): {snapshot['quiz_answers_last_24h']}\n"
        f"👥 Yangi referrallar (24s): {snapshot['referrals_last_24h']}\n\n"
        f"💾 JSON hajmi: {snapshot['json_total_size_kb']} KB "
        f"({snapshot['json_file_count']} fayl)\n"
        f"🗃 Kesh: {snapshot['cache_entries']}/{snapshot['cache_max_entries']} "
        f"(TTL: {snapshot['cache_ttl_seconds']}s)"
    )


@router.message(F.text.in_(("/devtools", "/dashboard")))
async def open_dashboard(message: Message) -> None:
    await message.answer(
        "🎛 <b>Interactive Admin Dashboard</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=dashboard_keyboard(),
    )


@router.callback_query(F.data == "dash:home")
async def dashboard_home(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🎛 <b>Interactive Admin Dashboard</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=dashboard_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "dash:health")
async def dashboard_health(callback: CallbackQuery, container: Container) -> None:
    text = await _build_health_text(container)
    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dash:stats")
async def dashboard_stats(callback: CallbackQuery, container: Container) -> None:
    data = await container.stats_service.summary()
    top_lines = "\n".join(
        f"  {i + 1}. {title} — {views} ko'rish"
        for i, (title, views) in enumerate(data["top_animes"])
    ) or "  —"

    text = (
        "📈 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {data['total_users']}\n"
        f"🚫 Bloklangan: {data['banned_users']}\n"
        f"🎬 Animelar: {data['total_animes']}\n"
        f"💎 Aktiv VIP: {data['active_vip']}\n"
        f"👁 Umumiy ko'rishlar: {data['total_views']}\n\n"
        f"🏆 <b>Top 5 anime:</b>\n{top_lines}"
    )
    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dash:vip")
async def dashboard_vip(callback: CallbackQuery, container: Container) -> None:
    pending = await container.vip_service.list_pending()
    text = f"💎 <b>Kutilayotgan VIP so'rovlar:</b> {len(pending)} ta\n\n"
    if pending:
        text += "To'liq ko'rish uchun asosiy menyudagi \"💎 VIP so'rovlar\" tugmasidan foydalaning."
    else:
        text += "Hozircha kutilayotgan so'rov yo'q."
    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dash:logs")
async def dashboard_logs(callback: CallbackQuery, container: Container) -> None:
    logs = await container.audit_service.recent(limit=10)
    if not logs:
        text = "📋 Loglar bo'sh."
    else:
        lines = ["📋 <b>Oxirgi 10 ta harakat:</b>\n"]
        for entry in logs:
            ts = entry["timestamp"][:16].replace("T", " ")
            lines.append(f"🕐 {ts} | {entry['action']} | actor={entry['actor_id']}")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "dash:repair")
async def dashboard_repair(callback: CallbackQuery, container: Container) -> None:
    await callback.answer("🔧 Tekshirilmoqda...")
    results = await container.maintenance_service.repair_all()
    repaired = [f for f, status in results.items() if status == "repaired"]

    if not repaired:
        text = f"✅ Barcha {len(results)} ta fayl sog'lom."
    else:
        text = f"🔧 Tuzatildi: {len(repaired)} ta fayl\n\n" + "\n".join(f"  • {f}" for f in repaired)

    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())


@router.callback_query(F.data == "dash:dedup")
async def dashboard_dedup(callback: CallbackQuery, container: Container) -> None:
    await callback.answer("🧹 Qidirilmoqda...")
    results = await container.maintenance_service.remove_duplicates_all()

    if not results:
        text = "✅ Hech qanday takroriy yozuv topilmadi."
    else:
        lines = [f"  • {f}: {count} ta o'chirildi" for f, count in results.items()]
        text = "🧹 Tozalandi:\n\n" + "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())


@router.callback_query(F.data == "dash:trash")
async def dashboard_trash(callback: CallbackQuery, container: Container) -> None:
    await callback.answer()
    removed = await container.maintenance_service.optimize_trash(keep_days=30)
    text = f"🗑 {removed} ta eski (30+ kunlik) o'chirilgan anime butunlay tozalandi."
    await callback.message.edit_text(text, reply_markup=dashboard_back_keyboard())


@router.callback_query(F.data == "dash:backup")
async def dashboard_backup(callback: CallbackQuery, container: Container) -> None:
    await callback.answer("💾 Backup yaratilmoqda...")
    zip_path = await container.backup_service.create_full_backup()
    await callback.message.answer_document(
        FSInputFile(zip_path),
        caption=f"✅ Backup tayyor: {zip_path.name}",
    )


# ---------------------------------------------------------------------------
# Eski matnli buyruqlar (backward-compatible, xohlagan admin ulardan ham
# foydalanishi mumkin)
# ---------------------------------------------------------------------------


@router.message(F.text == "/health")
async def show_health_cmd(message: Message, container: Container) -> None:
    text = await _build_health_text(container)
    await message.answer(text)


@router.message(F.text == "/jsonrepair")
async def repair_json_cmd(message: Message, container: Container) -> None:
    await message.answer("🔧 Fayllar tekshirilmoqda...")
    results = await container.maintenance_service.repair_all()
    repaired = [f for f, status in results.items() if status == "repaired"]
    if not repaired:
        await message.answer(f"✅ Barcha {len(results)} ta fayl sog'lom.")
        return
    await message.answer(
        f"🔧 Tuzatildi: {len(repaired)} ta fayl\n\n" + "\n".join(f"  • {f}" for f in repaired)
    )


@router.message(F.text == "/removeduplicates")
async def remove_duplicates_cmd(message: Message, container: Container) -> None:
    await message.answer("🧹 Takroriy yozuvlar qidirilmoqda...")
    results = await container.maintenance_service.remove_duplicates_all()
    if not results:
        await message.answer("✅ Hech qanday takroriy yozuv topilmadi.")
        return
    lines = [f"  • {f}: {count} ta o'chirildi" for f, count in results.items()]
    await message.answer("🧹 Tozalandi:\n\n" + "\n".join(lines))


@router.message(F.text == "/optimizetrash")
async def optimize_trash_cmd(message: Message, container: Container) -> None:
    removed = await container.maintenance_service.optimize_trash(keep_days=30)
    await message.answer(f"🗑 {removed} ta eski (30+ kunlik) o'chirilgan anime butunlay tozalandi.")
