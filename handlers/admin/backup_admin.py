"""💾 Backup yaratish/tiklash (faqat main-admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import BufferedInputFile, FSInputFile, Message

from config.enums import LogAction, Permission
from container import Container
from filters.admin_filters import IsAdmin, IsMainAdmin

router = Router(name="admin_backup")
router.message.filter(IsAdmin())


@router.message(F.text == "💾 Backup")
async def create_backup(message: Message, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.BACKUP_CREATE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    await message.answer("💾 Backup yaratilmoqda...")
    zip_path = await container.backup_service.create_full_backup()
    await container.audit_service.log(
        message.from_user.id, LogAction.BACKUP_CREATE, {"file": zip_path.name}
    )
    await message.answer_document(
        FSInputFile(zip_path), caption=f"✅ Backup tayyor: {zip_path.name}"
    )


@router.message(F.text == "/listbackups")
async def list_backups(message: Message, container: Container) -> None:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.BACKUP_CREATE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
        return

    backups = container.backup_service.list_backups()
    if not backups:
        await message.answer("💾 Hozircha hech qanday backup mavjud emas.")
        return

    lines = ["💾 <b>Mavjud backuplar:</b>\n"]
    for b in backups:
        size_kb = round(b.stat().st_size / 1024, 1)
        lines.append(f"• {b.name} ({size_kb} KB)")
    await message.answer("\n".join(lines))


backup_restore_router = Router(name="admin_backup_restore")
backup_restore_router.message.filter(IsMainAdmin())


@backup_restore_router.message(F.document, F.caption == "/restore_backup")
async def restore_backup(message: Message, container: Container) -> None:
    file = await message.bot.get_file(message.document.file_id)
    tmp_path = container.settings.backup_path / f"_incoming_{message.document.file_name}"
    await message.bot.download_file(file.file_path, destination=tmp_path)

    restored = await container.backup_service.restore_from_zip(tmp_path)
    await container.audit_service.log(
        message.from_user.id, LogAction.BACKUP_RESTORE, {"files": restored}
    )
    tmp_path.unlink(missing_ok=True)
    await message.answer(f"✅ Tiklandi: {len(restored)} ta fayl.\n\n" + "\n".join(restored))
