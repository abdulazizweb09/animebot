"""Tarjima (i18n) tizimi.

Barcha matnlar ``locales/*.json`` fayllarida. Kod ichida hech qachon
hardcoded matn yozilmaydi (adminlarga xos texnik xabarlardan tashqari) —
shu orqali yangi til qo'shish faqat yangi JSON fayl yozishni talab qiladi.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from config.enums import UserLanguage
from utils.logger import get_logger

logger = get_logger(__name__)

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


@lru_cache(maxsize=8)
def _load(language: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{language}.json"
    if not path.exists():
        logger.warning("Til fayli topilmadi: %s — default (uz) ishlatiladi", path)
        path = _LOCALES_DIR / f"{UserLanguage.default().value}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def all_variants(key: str) -> set[str]:
    """Berilgan kalit uchun BARCHA tillardagi tarjimalar to'plamini qaytaradi.

    Reply-keyboard tugmalarini matn bo'yicha aniqlashda ishlatiladi — chunki
    foydalanuvchi tili turlicha bo'lishi mumkin, lekin bosgan tugmasi
    aynan o'sha tildagi matn bo'ladi.
    """

    variants = set()
    for path in _LOCALES_DIR.glob("*.json"):
        lang = path.stem
        translations = _load(lang)
        if key in translations:
            variants.add(translations[key])
    return variants


def t(key: str, language: str = "uz", **kwargs) -> str:
    """Berilgan kalit va tilga mos matnni qaytaradi, ``{placeholder}`` larni
    to'ldiradi.
    """

    translations = _load(language)
    template = translations.get(key)
    if template is None:
        fallback = _load(UserLanguage.default().value)
        template = fallback.get(key, key)
        logger.warning("Tarjima topilmadi: key=%s lang=%s", key, language)
    try:
        return template.format(**kwargs)
    except KeyError as exc:
        logger.error("Tarjima uchun placeholder yetishmayapti: %s (%s)", key, exc)
        return template
