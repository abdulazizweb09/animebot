"""💾 To'liq backup (barcha JSON fayllarni ZIP qilish) va tiklash logikasi."""

from __future__ import annotations

import asyncio
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from config.constants import CONSTANTS
from database.json_manager import JsonManager
from database.schemas import ALL_JSON_FILES
from utils.logger import get_logger

logger = get_logger(__name__)


class BackupService:
    def __init__(self, manager: JsonManager, json_dir: Path, backup_dir: Path) -> None:
        self._manager = manager
        self._json_dir = json_dir
        self._backup_dir = backup_dir

    def _build_zip_sync(self, zip_path: Path) -> None:
        """ZIP arxivini yaratadi — sinxron ``zipfile`` amali, shuning uchun
        faqat ``asyncio.to_thread`` orqali chaqiriladi (event loop'ni
        bloklamaslik uchun, ayniqsa katta hajmdagi ma'lumotlarda).
        """

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename in ALL_JSON_FILES:
                file_path = self._json_dir / filename
                if file_path.exists():
                    zf.write(file_path, arcname=filename)

    async def create_full_backup(self) -> Path:
        """Barcha JSON fayllarni bitta ZIP arxivga yig'adi va yo'lini qaytaradi."""

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_path = self._backup_dir / f"full_backup_{timestamp}.zip"

        # zipfile — sinxron kutubxona, event loop'ni bloklamasligi uchun
        # alohida thread'da bajariladi.
        await asyncio.to_thread(self._build_zip_sync, zip_path)

        def _updater(data: dict) -> dict:
            data["last_backup_at"] = datetime.now(timezone.utc).isoformat()
            data["backup_count"] = data.get("backup_count", 0) + 1
            history = data.get("history", [])
            history.append({"file": zip_path.name, "at": data["last_backup_at"]})
            data["history"] = history[-CONSTANTS.BACKUP_KEEP_LAST_N :]
            return data

        await self._manager.update(
            "backup.json",
            _updater,
            default={"last_backup_at": None, "backup_count": 0, "history": []},
        )
        logger.info("To'liq backup yaratildi: %s", zip_path.name)
        await self._cleanup_old_backups()
        return zip_path

    async def _cleanup_old_backups(self) -> None:
        backups = await asyncio.to_thread(self.list_backups)
        for old in backups[CONSTANTS.BACKUP_KEEP_LAST_N :]:
            try:
                await asyncio.to_thread(old.unlink)
                logger.info("Eski backup o'chirildi: %s", old.name)
            except OSError as exc:
                logger.warning("Backup o'chirilmadi: %s (%s)", old.name, exc)

    def _restore_from_zip_sync(self, zip_path: Path) -> list[str]:
        """MUHIM (xavfsizlik): "Zip Slip" zaifligidan himoya.

        ZIP ichidagi fayl nomi ``../../etc/passwd`` kabi yo'l-o'tish
        belgilarini o'z ichiga olishi mumkin — agar tekshirilmasa, fayl
        ``json_dir`` tashqarisiga (masalan, tizim fayllari ustiga)
        yozilib ketishi mumkin edi. Shu sabab har bir yozuv uchun:
            1. Nomi ALL_JSON_FILES oq ro'yxatida bo'lishi shart
               (ixtiyoriy "evil.json" fayl yozilishining oldini oladi).
            2. Yakuniy yo'l ``json_dir`` ichida qolishi ``resolve()`` bilan
               qat'iy tekshiriladi.
        """

        from database.schemas import ALL_JSON_FILES

        json_dir_resolved = self._json_dir.resolve()
        restored: list[str] = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if name not in ALL_JSON_FILES:
                    logger.warning("Backup'da noma'lum/ruxsatsiz fayl e'tiborsiz qoldirildi: %s", name)
                    continue

                target = (self._json_dir / name).resolve()
                if not target.is_relative_to(json_dir_resolved):
                    logger.error("Zip Slip urinishi aniqlandi va bloklandi: %s", name)
                    continue

                with zf.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                restored.append(name)
        return restored

    async def restore_from_zip(self, zip_path: Path) -> list[str]:
        """ZIP ichidagi JSON fayllarni ``json_dir`` ga tiklaydi. Tiklangan fayllar
        ro'yxatini qaytaradi.
        """

        # zipfile + fayl nusxalash — sinxron, shuning uchun thread'da.
        restored = await asyncio.to_thread(self._restore_from_zip_sync, zip_path)

        for name in restored:
            self._manager.cache_clear(name)

        logger.info("Backup tiklandi: %d ta fayl", len(restored))
        return restored

    def list_backups(self) -> list[Path]:
        return sorted(self._backup_dir.glob("full_backup_*.zip"), reverse=True)
