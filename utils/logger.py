"""Markazlashtirilgan logging konfiguratsiyasi.

Loyihadagi har bir modul ``get_logger(__name__)`` orqali logger oladi.
Loglar konsolga va ``logs/bot.log`` (kunlik rotatsiya bilan) fayliga yoziladi.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_CONFIGURED = False

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(log_dir: Path, level: str = "INFO") -> None:
    """Root logger'ni bir marta sozlaydi. Qayta chaqirilsa hech narsa qilmaydi."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    file_handler = TimedRotatingFileHandler(
        filename=str(log_dir / "bot.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    error_handler = TimedRotatingFileHandler(
        filename=str(log_dir / "errors.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    root.addHandler(error_handler)

    # Uchinchi-tomon kutubxonalarning ortiqcha DEBUG loglarini bostirish
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Berilgan modul nomi uchun logger qaytaradi."""

    return logging.getLogger(name)
