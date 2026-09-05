"""📊 Statistika (admin)."""

from __future__ import annotations

import csv
import io

from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message

from container import Container
from filters.admin_filters import IsAdmin

router = Router(name="admin_stats")
router.message.filter(IsAdmin())


@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message, container: Container) -> None:
    data = await container.stats_service.summary()
    top_lines = "\n".join(f"  {i+1}. {title} — {views} ko'rish" for i, (title, views) in enumerate(data["top_animes"])) or "  —"

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {data['total_users']}\n"
        f"🚫 Bloklangan: {data['banned_users']}\n"
        f"🎬 Animelar: {data['total_animes']}\n"
        f"💎 Aktiv VIP: {data['active_vip']}\n"
        f"👁 Umumiy ko'rishlar: {data['total_views']}\n\n"
        f"🏆 <b>Top 5 anime:</b>\n{top_lines}\n\n"
        f"📤 To'liq jadval uchun: /exportstats"
    )
    await message.answer(text)


@router.message(F.text == "/exportstats")
async def export_stats_csv(message: Message, container: Container) -> None:
    """Barcha animelarning to'liq statistikasini CSV fayl sifatida
    eksport qiladi — admin hisobot/tahlil uchun Excelga ochishi mumkin.
    """

    animes = await container.animes.all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Kod", "Nomi", "Yil", "Janrlar", "Studiya", "Ko'rishlar", "O'rtacha baho", "Baholar soni", "Holat"]
    )
    for a in sorted(animes, key=lambda x: x.views, reverse=True):
        writer.writerow(
            [
                a.code,
                a.title_uz,
                a.year or "",
                ", ".join(a.genres),
                a.studio or "",
                a.views,
                a.average_rating,
                a.rating_count,
                a.status,
            ]
        )

    file_bytes = buffer.getvalue().encode("utf-8-sig")  # BOM — Excelda to'g'ri ochilishi uchun
    await message.answer_document(
        BufferedInputFile(file_bytes, filename="anime_statistics.csv"),
        caption=f"📤 {len(animes)} ta anime bo'yicha to'liq statistika.",
    )
