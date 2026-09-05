"""Foydalanuvchi bo'yicha oxirgi ro'yxat natijalarini xotirada saqlaydi.

Pagination callback_data uzunligi cheklangani uchun (Telegram — 64 bayt),
to'liq qidiruv/kategoriya natijalarini callback_data ichiga sig'dirib
bo'lmaydi. Shuning uchun natijalar shu yerda ``(user_id, context)`` kaliti
bilan xotirada saqlanadi, callback esa faqat ``context`` va ``page``
raqamini yuboradi.

Eslatma: bu process-xotirasida ishlaydi (Redis emas), bot qayta ishga
tushganda tozalanadi — bu qidiruv natijalari kabi vaqtinchalik ma'lumot
uchun yetarli.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class _Entry:
    codes: list[str]
    expires_at: float


class ListCacheService:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl = ttl_seconds
        self._store: dict[tuple[int, str], _Entry] = {}

    def set(self, user_id: int, context: str, codes: list[str]) -> None:
        self._store[(user_id, context)] = _Entry(
            codes=codes, expires_at=time.monotonic() + self._ttl
        )

    def get(self, user_id: int, context: str) -> list[str] | None:
        entry = self._store.get((user_id, context))
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            self._store.pop((user_id, context), None)
            return None
        return entry.codes
