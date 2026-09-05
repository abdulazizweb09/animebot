"""``.env`` faylidan sozlamalarni o'qiydigan yagona joy.

Boshqa hech qaysi modul ``os.getenv`` ni to'g'ridan-to'g'ri chaqirmasligi
kerak — faqat ``get_settings()`` orqali.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from config.enums import VipPlan


class SettingsError(Exception):
    """Sozlamalar noto'g'ri yoki yetishmayotganda ko'tariladi."""


def _parse_int_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    result: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            result.append(int(chunk))
        except ValueError as exc:
            raise SettingsError(
                f"Noto'g'ri ID qiymati '.env' faylida: {chunk!r}"
            ) from exc
    return result


def _require(name: str, raw: str | None) -> str:
    if raw is None or raw.strip() == "":
        raise SettingsError(
            f"'{name}' o'zgaruvchisi .env faylida topilmadi yoki bo'sh. "
            f".env.example faylini nusxalab, qiymatlarni to'ldiring."
        )
    return raw.strip()


def _parse_float(name: str, raw: str | None, default: float) -> float:
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise SettingsError(f"'{name}' float bo'lishi kerak, olindi: {raw!r}") from exc


def _parse_int(name: str, raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise SettingsError(f"'{name}' int bo'lishi kerak, olindi: {raw!r}") from exc


@dataclass(frozen=True)
class VipPricing:
    """Har bir VIP plan uchun narx (so'mda)."""

    prices: dict[VipPlan, int]

    def price_for(self, plan: VipPlan) -> int:
        return self.prices[plan]


@dataclass(frozen=True)
class RateLimitSettings:
    default_seconds: float
    vip_seconds: float
    ai_per_minute: int
    search_per_minute: int


@dataclass(frozen=True)
class FloodSettings:
    max_messages: int
    window_seconds: int
    ban_seconds: int


@dataclass(frozen=True)
class Settings:
    """Bot uchun barcha sozlamalarning yagona manbasi (immutable)."""

    bot_token: str
    main_admin_ids: list[int]
    admin_ids: list[int]
    channel_id: int | None
    support_id: int | None

    gemini_api_key: str
    gemini_model: str

    vip_pricing: VipPricing

    base_dir: Path
    json_dir: Path
    backup_path: Path
    log_dir: Path

    log_level: str

    rate_limit: RateLimitSettings
    flood: FloodSettings

    @property
    def all_admin_ids(self) -> set[int]:
        return set(self.main_admin_ids) | set(self.admin_ids)

    def is_main_admin(self, user_id: int) -> bool:
        return user_id in self.main_admin_ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.all_admin_ids


def _load_settings() -> Settings:
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    bot_token = _require("BOT_TOKEN", os.getenv("BOT_TOKEN"))
    gemini_api_key = _require("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

    main_admin_ids = _parse_int_list(os.getenv("MAIN_ADMIN_IDS"))
    admin_ids = _parse_int_list(os.getenv("ADMIN_IDS"))

    if not main_admin_ids:
        raise SettingsError(
            "'MAIN_ADMIN_IDS' bo'sh bo'lishi mumkin emas — kamida bitta "
            "asosiy admin ID kerak."
        )

    channel_raw = os.getenv("CHANNEL_ID")
    support_raw = os.getenv("SUPPORT_ID")

    vip_pricing = VipPricing(
        prices={
            VipPlan.ONE_MONTH: _parse_int(
                "VIP_PRICE_1_MONTH", os.getenv("VIP_PRICE_1_MONTH"), 25000
            ),
            VipPlan.THREE_MONTHS: _parse_int(
                "VIP_PRICE_3_MONTH", os.getenv("VIP_PRICE_3_MONTH"), 65000
            ),
            VipPlan.SIX_MONTHS: _parse_int(
                "VIP_PRICE_6_MONTH", os.getenv("VIP_PRICE_6_MONTH"), 120000
            ),
            VipPlan.TWELVE_MONTHS: _parse_int(
                "VIP_PRICE_12_MONTH", os.getenv("VIP_PRICE_12_MONTH"), 220000
            ),
        }
    )

    json_dir = base_dir / os.getenv("JSON_DIR", "json")
    backup_path = base_dir / os.getenv("BACKUP_PATH", "backup")
    log_dir = base_dir / os.getenv("LOG_DIR", "logs")

    for directory in (json_dir, backup_path, log_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rate_limit = RateLimitSettings(
        default_seconds=_parse_float(
            "RATE_LIMIT_DEFAULT", os.getenv("RATE_LIMIT_DEFAULT"), 1.0
        ),
        vip_seconds=_parse_float("RATE_LIMIT_VIP", os.getenv("RATE_LIMIT_VIP"), 0.3),
        ai_per_minute=_parse_int(
            "RATE_LIMIT_AI_PER_MINUTE", os.getenv("RATE_LIMIT_AI_PER_MINUTE"), 10
        ),
        search_per_minute=_parse_int(
            "RATE_LIMIT_SEARCH_PER_MINUTE",
            os.getenv("RATE_LIMIT_SEARCH_PER_MINUTE"),
            20,
        ),
    )

    flood = FloodSettings(
        max_messages=_parse_int(
            "FLOOD_MAX_MESSAGES", os.getenv("FLOOD_MAX_MESSAGES"), 5
        ),
        window_seconds=_parse_int(
            "FLOOD_WINDOW_SECONDS", os.getenv("FLOOD_WINDOW_SECONDS"), 10
        ),
        ban_seconds=_parse_int(
            "FLOOD_BAN_SECONDS", os.getenv("FLOOD_BAN_SECONDS"), 30
        ),
    )

    return Settings(
        bot_token=bot_token,
        main_admin_ids=main_admin_ids,
        admin_ids=admin_ids,
        channel_id=int(channel_raw) if channel_raw else None,
        support_id=int(support_raw) if support_raw else None,
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip(),
        vip_pricing=vip_pricing,
        base_dir=base_dir,
        json_dir=json_dir,
        backup_path=backup_path,
        log_dir=log_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        rate_limit=rate_limit,
        flood=flood,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Sozlamalarni bir marta o'qiydi va keshda saqlaydi (singleton)."""

    return _load_settings()
