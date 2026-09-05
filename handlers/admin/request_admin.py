"""🎬 Anime so'rovlari va 🐛 Bug-reportlarni ko'rish/hal qilish — admin."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin

router = Router(name="admin_request")
router.message.filter(IsAdmin())


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.REQUEST_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


@router.message(F.text == "🎬 Anime so'rovlari")
async def list_anime_requests(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    pending = await container.anime_request_service.list_pending()
    if not pending:
        await message.answer("🎬 Kutilayotgan so'rov yo'q.")
        return

    lines = ["🎬 <b>Kutilayotgan anime so'rovlari:</b>\n"]
    for r in pending[:20]:
        votes = len(r.upvoted_by)
        vote_text = f" 👍{votes}" if votes else ""
        lines.append(f"• <code>{r.id[:8]}</code> — {r.title}{vote_text} (user: {r.user_id})")
    lines.append(
        "\n✅ Bajarish: /fulfillrequest <id_boshi>"
        "\n❌ Rad etish: /rejectrequest <id_boshi>"
    )
    await message.answer("\n".join(lines))


async def _find_request_by_prefix(container: Container, prefix: str):
    pending = await container.anime_request_service.list_pending()
    for r in pending:
        if r.id.startswith(prefix):
            return r
    return None


@router.message(F.text.startswith("/fulfillrequest "))
async def fulfill_request(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    prefix = message.text.split(" ", 1)[1].strip()
    request = await _find_request_by_prefix(container, prefix)
    if request is None:
        await message.answer("❌ So'rov topilmadi.")
        return

    await container.anime_request_service.decide(request.id, "fulfilled", message.from_user.id)

    interested_users = {request.user_id} | set(request.upvoted_by)
    for user_id in interested_users:
        try:
            await message.bot.send_message(
                user_id, f"🎉 Siz so'ragan '{request.title}' anime botga qo'shildi!"
            )
        except Exception:  # noqa: BLE001
            pass

    await message.answer(
        f"✅ So'rov bajarildi deb belgilandi: {request.title} "
        f"({len(interested_users)} kishiga xabar berildi)"
    )


@router.message(F.text.startswith("/rejectrequest "))
async def reject_request(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    prefix = message.text.split(" ", 1)[1].strip()
    request = await _find_request_by_prefix(container, prefix)
    if request is None:
        await message.answer("❌ So'rov topilmadi.")
        return

    await container.anime_request_service.decide(request.id, "rejected", message.from_user.id)
    await message.answer(f"❌ So'rov rad etildi: {request.title}")


@router.message(F.text == "🐛 Bug-reportlar")
async def list_bug_reports(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    open_reports = await container.bug_report_service.list_open()
    if not open_reports:
        await message.answer("🐛 Ochiq muammo yo'q.")
        return

    lines = ["🐛 <b>Ochiq muammolar:</b>\n"]
    for r in open_reports[:20]:
        lines.append(f"• <code>{r.id[:8]}</code> (user: {r.user_id}): {r.text[:100]}")
    lines.append("\n✅ Hal qilingan deb belgilash: /resolvebug <id_boshi>")
    await message.answer("\n".join(lines))


@router.message(F.text.startswith("/resolvebug "))
async def resolve_bug(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    prefix = message.text.split(" ", 1)[1].strip()
    open_reports = await container.bug_report_service.list_open()
    report = next((r for r in open_reports if r.id.startswith(prefix)), None)
    if report is None:
        await message.answer("❌ Muammo topilmadi.")
        return

    await container.bug_report_service.resolve(report.id, message.from_user.id)
    await message.answer("✅ Hal qilindi deb belgilandi.")


# ---------------------------------------------------------------------------
# 💬 Izohlarni moderatsiya qilish
# ---------------------------------------------------------------------------


@router.message(F.text == "/moderatecomments")
async def list_comments_for_moderation(message: Message, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.COMMENT_MODERATE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    comments = await container.comment_service.recent_for_moderation(limit=20)
    reported = await container.comment_service.list_most_reported(limit=10)

    lines = []
    if reported:
        lines.append("🚩 <b>Shikoyat qilinganlar:</b>\n")
        for c in reported:
            lines.append(
                f"• <code>{c.id[:8]}</code> [{c.anime_code}] user={c.user_id} "
                f"(🚩{len(c.reported_by)}): {c.text[:80]}"
            )
        lines.append("")

    if not comments and not reported:
        await message.answer("💬 Izohlar yo'q.")
        return

    lines.append("💬 <b>So'nggi izohlar:</b>\n")
    for c in comments:
        lines.append(
            f"• <code>{c.id[:8]}</code> [{c.anime_code}] user={c.user_id}: {c.text[:80]}"
        )
    lines.append("\n🗑 O'chirish: /deletecomment <id_boshi>")
    await message.answer("\n".join(lines))


@router.message(F.text.startswith("/deletecomment "))
async def delete_comment_admin(message: Message, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.COMMENT_MODERATE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    prefix = message.text.split(" ", 1)[1].strip()
    comments = await container.comment_service.recent_for_moderation(limit=200)
    comment = next((c for c in comments if c.id.startswith(prefix)), None)
    if comment is None:
        await message.answer("❌ Izoh topilmadi.")
        return

    await container.comment_service.delete_comment(comment.id, message.from_user.id, is_admin=True)
    await message.answer("✅ Izoh o'chirildi.")
