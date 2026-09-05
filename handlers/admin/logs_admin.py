"""📋 Audit loglarni ko'rish (admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin

router = Router(name="admin_logs")
router.message.filter(IsAdmin())


@router.message(F.text == "📋 Loglar")
async def show_logs(message: Message, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.LOGS_VIEW
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    logs = await container.audit_service.recent(limit=20)
    if not logs:
        await message.answer("📋 Loglar bo'sh.")
        return

    lines = []
    for entry in logs:
        ts = entry["timestamp"][:16].replace("T", " ")
        lines.append(f"🕐 {ts} | {entry['action']} | actor={entry['actor_id']}")
    await message.answer("📋 Oxirgi harakatlar:\n\n" + "\n".join(lines))
