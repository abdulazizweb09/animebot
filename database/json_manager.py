"""``JsonManager`` — loyihadagi JSON fayllar bilan ishlaydigan YAGONA klass.

Qoida: boshqa hech qaysi modul (repository'lardan tashqari) to'g'ridan-to'g'ri
``open()``, ``json.load`` yoki ``json.dump`` chaqirmasin. Faqat shu klass
orqali.

Xavfsizlik kafolatlari:
    * **Atomic write** — avval ``.tmp`` faylga yoziladi, so'ng ``os.replace``
      bilan asl faylga almashtiriladi. Shu tufayli yozish jarayonida elektr
      o'chib qolsa ham, asl fayl yarim yozilgan holda qolmaydi.
    * **Per-file async lock** — bir xil faylga bir vaqtning o'zida ikkita
      yozish amali bo'lishining oldini oladi (race condition yo'q).
    * **In-memory cache (TTL)** — tez-tez o'qiladigan fayllar diskdan qayta-
      qayta o'qilmaydi.
    * **Auto-create** — fayl mavjud bo'lmasa, standart qiymat bilan avtomatik
      yaratiladi.
    * **Backup/restore** — istalgan faylning versiyalangan nusxasini olish va
      undan tiklash imkoniyati.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import aiofiles

from utils.exceptions import (
    JsonCorruptedError,
    JsonLockTimeoutError,
    JsonNotFoundError,
    JsonValidationError,
)
from utils.logger import get_logger

logger = get_logger(__name__)

JsonType = dict[str, Any] | list[Any]
Validator = Callable[[JsonType], bool]


@dataclass
class _CacheEntry:
    value: JsonType
    expires_at: float


class JsonManager:
    """JSON fayllar bilan xavfsiz, keshlangan, atomic ishlaydigan menejer.

    Bitta instansiya butun bot davomida (``bot.data`` yoki DI konteyner
    orqali) qayta ishlatiladi, chunki lock va cache holatlari instansiya
    ichida saqlanadi.
    """

    def __init__(
        self,
        base_dir: Path,
        backup_dir: Path | None = None,
        cache_ttl_seconds: int = 300,
        cache_max_entries: int = 512,
        lock_timeout_seconds: float = 10.0,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

        self._backup_dir = Path(backup_dir) if backup_dir else self._base_dir / "_backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        self._cache_ttl = cache_ttl_seconds
        self._cache_max_entries = cache_max_entries
        self._lock_timeout = lock_timeout_seconds

        self._cache: dict[str, _CacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

        self._validators: dict[str, Validator] = {}

        logger.info("JsonManager ishga tushdi. base_dir=%s", self._base_dir)

    # ------------------------------------------------------------------
    # Yordamchi (private) metodlar
    # ------------------------------------------------------------------

    def _path(self, filename: str) -> Path:
        if not filename.endswith(".json"):
            filename = f"{filename}.json"
        return self._base_dir / filename

    async def _get_lock(self, filename: str) -> asyncio.Lock:
        """Fayl uchun mos ``asyncio.Lock`` ni qaytaradi (kerak bo'lsa yaratadi)."""

        async with self._locks_guard:
            lock = self._locks.get(filename)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[filename] = lock
            return lock

    def _cache_get(self, filename: str) -> JsonType | None:
        entry = self._cache.get(filename)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            self._cache.pop(filename, None)
            return None
        return entry.value

    def _cache_set(self, filename: str, value: JsonType) -> None:
        if len(self._cache) >= self._cache_max_entries and filename not in self._cache:
            # Eng eski yozuvni chiqarib tashlash (oddiy FIFO-ga yaqin strategiya)
            oldest_key = next(iter(self._cache), None)
            if oldest_key is not None:
                self._cache.pop(oldest_key, None)
        self._cache[filename] = _CacheEntry(
            value=value, expires_at=time.monotonic() + self._cache_ttl
        )

    def _cache_invalidate(self, filename: str) -> None:
        self._cache.pop(filename, None)

    @staticmethod
    def _deep_copy(data: JsonType) -> JsonType:
        # json orqali deep-copy — kesh obyektini tashqariga tegishga yo'l qo'ymaslik
        return json.loads(json.dumps(data, ensure_ascii=False))

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def register_validator(self, filename: str, validator: Validator) -> None:
        """Berilgan fayl uchun yozishdan oldin ishlaydigan validatorni ro'yxatdan
        o'tkazadi. Validator ``False`` qaytarsa yoki xato ko'tarsa, yozish
        bekor qilinadi.
        """

        key = filename if filename.endswith(".json") else f"{filename}.json"
        self._validators[key] = validator

    def _validate(self, filename: str, data: JsonType) -> None:
        key = filename if filename.endswith(".json") else f"{filename}.json"
        validator = self._validators.get(key)
        if validator is None:
            return
        try:
            is_valid = validator(data)
        except Exception as exc:  # noqa: BLE001 — validatordan kelgan har qanday xato
            raise JsonValidationError(
                f"'{key}' uchun validatsiya funksiyasi xato berdi: {exc}"
            ) from exc
        if not is_valid:
            raise JsonValidationError(f"'{key}' fayli validatsiyadan o'tmadi.")

    # ------------------------------------------------------------------
    # Asosiy public API
    # ------------------------------------------------------------------

    async def exists(self, filename: str) -> bool:
        """Fayl diskda mavjudligini tekshiradi."""

        return await asyncio.to_thread(self._path(filename).exists)

    def file_size(self, filename: str) -> int:
        """Faylning disk hajmini (bayt) qaytaradi, mavjud bo'lmasa 0.

        Eslatma: bu metod ataylab SYNC qoldirilgan — faqat kamdan-kam
        (admin diagnostika/health-check) chaqiriladi, hot-path emas.
        """

        path = self._path(filename)
        return path.stat().st_size if path.exists() else 0

    async def auto_create(self, filename: str, default: JsonType) -> None:
        """Fayl mavjud bo'lmasa, ``default`` qiymat bilan yaratadi.

        Bot ishga tushganda barcha kerakli JSON fayllar uchun chaqiriladi,
        shunda birinchi marta ishga tushirilganda ham hech qanday
        "fayl topilmadi" xatosi bo'lmaydi.
        """

        path = self._path(filename)
        if await asyncio.to_thread(path.exists):
            return
        lock = await self._get_lock(filename)
        async with lock:
            if await asyncio.to_thread(path.exists):  # double-check (race condition oldini olish)
                return
            await self._atomic_write_unlocked(filename, default)
            logger.info("JSON fayl avtomatik yaratildi: %s", filename)

    async def read(
        self,
        filename: str,
        default: JsonType | None = None,
        use_cache: bool = True,
    ) -> JsonType:
        """Faylni o'qiydi. Fayl yo'q bo'lsa va ``default`` berilgan bo'lsa,
        avtomatik yaratadi va uni qaytaradi.
        """

        if use_cache:
            cached = self._cache_get(filename)
            if cached is not None:
                return self._deep_copy(cached)

        path = self._path(filename)

        if not await asyncio.to_thread(path.exists):
            if default is not None:
                await self.auto_create(filename, default)
                return self._deep_copy(default)
            raise JsonNotFoundError(f"JSON fayl topilmadi: {filename}")

        lock = await self._get_lock(filename)
        try:
            async with asyncio.timeout(self._lock_timeout):
                async with lock:
                    data = await self._read_raw(path, filename)
        except TimeoutError as exc:
            raise JsonLockTimeoutError(
                f"'{filename}' faylini o'qishda lock timeout bo'ldi."
            ) from exc

        if use_cache:
            self._cache_set(filename, data)
        return self._deep_copy(data)

    async def _read_raw(self, path: Path, filename: str) -> JsonType:
        try:
            async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
                content = await f.read()
        except OSError as exc:
            raise JsonNotFoundError(f"'{filename}' o'qib bo'lmadi: {exc}") from exc

        if not content.strip():
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("JSON buzilgan: %s — %s", filename, exc)
            raise JsonCorruptedError(
                f"'{filename}' fayli buzilgan (JSON parse xatosi): {exc}"
            ) from exc

    async def write(self, filename: str, data: JsonType) -> None:
        """Butun faylni yangi ``data`` bilan to'liq almashtiradi (atomic)."""

        self._validate(filename, data)
        lock = await self._get_lock(filename)
        try:
            async with asyncio.timeout(self._lock_timeout):
                async with lock:
                    await self._atomic_write_unlocked(filename, data)
        except TimeoutError as exc:
            raise JsonLockTimeoutError(
                f"'{filename}' faylini yozishda lock timeout bo'ldi."
            ) from exc
        self._cache_set(filename, data)

    async def atomic_write(self, filename: str, data: JsonType) -> None:
        """``write`` bilan bir xil — tashqi kod uchun aniqroq nom sifatida."""

        await self.write(filename, data)

    async def _atomic_write_unlocked(self, filename: str, data: JsonType) -> None:
        """Lock allaqachon olingan holatda chaqiriladigan ichki yozuvchi.

        Strategiya: ``file.json.tmp`` ga yozib, ``fsync`` qilib, keyin
        ``os.replace`` bilan asl nomga almashtiramiz. ``os.replace`` POSIX va
        Windows'da atomic operatsiya hisoblanadi — shu tufayli yozish
        jarayonida jarayon to'xtab qolsa ham, asl fayl hech qachon yarim
        yozilgan holatda qolmaydi.

        MUHIM: ``os.fsync`` va ``os.replace`` — bloklovchi (sinxron) syscall'lar.
        100 000+ foydalanuvchi bilan ishlaydigan botda ularni to'g'ridan-to'g'ri
        async funksiya ichida chaqirish event loop'ni vaqtincha to'xtatib
        qo'yishi mumkin (ayniqsa fsync disk I/O kutadi). Shuning uchun ikkalasi
        ham ``asyncio.to_thread`` orqali alohida thread'da bajariladi — event
        loop hech qachon disk operatsiyasini kutib bloklanmaydi.

        Windows'da ``os.replace`` boshqa jarayon/antivirus faylni vaqtincha
        band qilib turgan bo'lsa ``PermissionError`` berishi mumkin (bu odatda
        millisekundlar davomida o'tib ketadigan vaqtinchalik holat). Shu sabab
        qisqa backoff bilan bir necha marta qayta urinamiz.
        """

        path = self._path(filename)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        serialized = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)

        async with aiofiles.open(tmp_path, mode="w", encoding="utf-8") as f:
            await f.write(serialized)
            await f.flush()
            await asyncio.to_thread(os.fsync, f.fileno())

        await self._replace_with_retry(tmp_path, path)
        self._cache_invalidate(filename)
        logger.debug("JSON yozildi: %s (%d belgi)", filename, len(serialized))

    @staticmethod
    async def _replace_with_retry(
        tmp_path: Path, target_path: Path, max_attempts: int = 5
    ) -> None:
        """``os.replace``ni thread'da, vaqtinchalik xatolarda qayta urinish
        bilan bajaradi (Windows'da ``PermissionError``/``FileInUseError``
        holatlari uchun).
        """

        last_exc: OSError | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                await asyncio.to_thread(os.replace, tmp_path, target_path)
                return
            except (PermissionError, OSError) as exc:
                last_exc = exc
                if attempt == max_attempts:
                    break
                # Eksponensial backoff: 50ms, 100ms, 200ms, 400ms...
                await asyncio.sleep(0.05 * (2 ** (attempt - 1)))
                logger.warning(
                    "os.replace muvaffaqiyatsiz (urinish %d/%d): %s — qayta urinilmoqda",
                    attempt,
                    max_attempts,
                    exc,
                )

        # Barcha urinishlar muvaffaqiyatsiz bo'lsa — .tmp faylni tozalashga
        # harakat qilamiz va asl xatoni tashqariga chiqaramiz.
        try:
            if tmp_path.exists():
                await asyncio.to_thread(tmp_path.unlink)
        except OSError:
            pass
        raise last_exc  # type: ignore[misc]

    async def update(
        self,
        filename: str,
        updater: Callable[[JsonType], JsonType],
        default: JsonType | None = None,
    ) -> JsonType:
        """Read-modify-write amalini bitta lock ostida atomik bajaradi.

        ``updater`` — joriy ma'lumotni qabul qilib, yangilangan ma'lumotni
        qaytaruvchi (sync yoki async bo'lishi mumkin) funksiya. Bu race
        condition'siz "o'qi -> o'zgartir -> yoz" ketma-ketligini kafolatlaydi.
        """

        lock = await self._get_lock(filename)
        try:
            async with asyncio.timeout(self._lock_timeout):
                async with lock:
                    path = self._path(filename)
                    if not await asyncio.to_thread(path.exists):
                        if default is None:
                            raise JsonNotFoundError(
                                f"JSON fayl topilmadi: {filename}"
                            )
                        current = self._deep_copy(default)
                    else:
                        current = await self._read_raw(path, filename)

                    result = updater(current)
                    if asyncio.iscoroutine(result):
                        result = await result

                    self._validate(filename, result)
                    await self._atomic_write_unlocked(filename, result)
        except TimeoutError as exc:
            raise JsonLockTimeoutError(
                f"'{filename}' faylini yangilashda lock timeout bo'ldi."
            ) from exc

        self._cache_set(filename, result)
        return self._deep_copy(result)

    async def delete(self, filename: str) -> bool:
        """Faylni diskdan o'chiradi. Fayl bo'lmasa ``False`` qaytaradi."""

        lock = await self._get_lock(filename)
        async with lock:
            path = self._path(filename)
            if not await asyncio.to_thread(path.exists):
                return False
            await asyncio.to_thread(path.unlink)
            self._cache_invalidate(filename)
            logger.info("JSON fayl o'chirildi: %s", filename)
            return True

    async def backup(self, filename: str) -> Path:
        """Faylning joriy holatini ``_backups/<filename>.<timestamp>.json``
        sifatida saqlaydi va yo'lini qaytaradi.
        """

        path = self._path(filename)
        if not await asyncio.to_thread(path.exists):
            raise JsonNotFoundError(f"Backup uchun fayl topilmadi: {filename}")

        lock = await self._get_lock(filename)
        async with lock:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.stem}.{timestamp}.json"
            backup_path = self._backup_dir / backup_name
            await asyncio.to_thread(shutil.copy2, path, backup_path)
            logger.info("Backup yaratildi: %s -> %s", filename, backup_path.name)
            return backup_path

    async def restore(self, filename: str, backup_path: Path) -> None:
        """Berilgan backup fayldan asl faylni tiklaydi (atomic)."""

        backup_path = Path(backup_path)
        if not await asyncio.to_thread(backup_path.exists):
            raise JsonNotFoundError(f"Backup fayl topilmadi: {backup_path}")

        try:
            async with aiofiles.open(backup_path, mode="r", encoding="utf-8") as f:
                content = await f.read()
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise JsonCorruptedError(
                f"Backup fayli buzilgan: {backup_path} — {exc}"
            ) from exc

        await self.write(filename, data)
        logger.info("Fayl tiklandi: %s <- %s", filename, backup_path.name)

    def cache_clear(self, filename: str | None = None) -> None:
        """Keshni tozalaydi. ``filename`` berilmasa — butun keshni tozalaydi."""

        if filename is None:
            self._cache.clear()
        else:
            self._cache_invalidate(filename)

    def cache_stats(self) -> dict[str, int]:
        """Monitoring/health-check uchun kesh statistikasi."""

        return {
            "entries": len(self._cache),
            "max_entries": self._cache_max_entries,
            "ttl_seconds": self._cache_ttl,
        }
