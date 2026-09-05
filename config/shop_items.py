"""Tanga Do'koni (Coin Shop) — tanga evaziga sotib olinadigan narsalar.

Bu economy tizimidagi "sink" (chiqim) qismi — avval tangalar faqat
to'planardi (epizod ko'rish, kunlik bonus, referral), lekin ularni
sarflashning umuman iloji yo'q edi. Endi foydalanuvchilar to'plagan
tangalarini haqiqiy foydaga aylantira olishadi.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShopItem:
    code: str
    label: str
    description: str
    price_coins: int
    kind: str  # "vip_days" | "profile_badge"
    value: int = 0  # vip_days uchun kunlar soni


SHOP_ITEMS: dict[str, ShopItem] = {
    "vip_1day": ShopItem(
        code="vip_1day",
        label="💎 1 kunlik VIP",
        description="1 kunlik VIP obuna",
        price_coins=500,
        kind="vip_days",
        value=1,
    ),
    "vip_3day": ShopItem(
        code="vip_3day",
        label="💎 3 kunlik VIP",
        description="3 kunlik VIP obuna",
        price_coins=1300,
        kind="vip_days",
        value=3,
    ),
    "vip_7day": ShopItem(
        code="vip_7day",
        label="💎 7 kunlik VIP",
        description="7 kunlik VIP obuna",
        price_coins=2800,
        kind="vip_days",
        value=7,
    ),
}


def get_shop_item(code: str) -> ShopItem | None:
    return SHOP_ITEMS.get(code)
