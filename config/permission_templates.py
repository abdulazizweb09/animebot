"""Tayyor ruxsat shablonlari — tez admin tayinlash uchun.

Har safar 10+ ta ruxsatni bittalab yoqish o'rniga, main-admin bitta
shablonni tanlab, tayyor ruxsatlar to'plamini bir zumda beradi.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.enums import Permission


@dataclass(frozen=True)
class PermissionTemplate:
    code: str
    label: str
    description: str
    permissions: tuple[Permission, ...]


TEMPLATES: dict[str, PermissionTemplate] = {
    "moderator": PermissionTemplate(
        code="moderator",
        label="🛡 Moderator",
        description="Izohlarni moderatsiya qilish, foydalanuvchilarni ban qilish, so'rovlarni ko'rish",
        permissions=(
            Permission.COMMENT_MODERATE,
            Permission.USER_BAN,
            Permission.REQUEST_MANAGE,
            Permission.USER_LOOKUP,
        ),
    ),
    "content_manager": PermissionTemplate(
        code="content_manager",
        label="🎬 Kontent menejeri",
        description="Anime, video, kolleksiya, jadval va qo'shimcha kontent qo'shish/tahrirlash",
        permissions=(
            Permission.ANIME_ADD,
            Permission.ANIME_EDIT,
            Permission.ANIME_DELETE,
            Permission.VIDEO_ADD,
            Permission.VIDEO_DELETE,
            Permission.COLLECTION_MANAGE,
            Permission.SCHEDULE_MANAGE,
            Permission.CONTENT_MANAGE,
        ),
    ),
    "support": PermissionTemplate(
        code="support",
        label="🎧 Support",
        description="Foydalanuvchi qidirish, VIP so'rovlarni tasdiqlash, so'rov/xatoliklarni ko'rish",
        permissions=(
            Permission.USER_LOOKUP,
            Permission.VIP_APPROVE,
            Permission.REQUEST_MANAGE,
        ),
    ),
    "marketing": PermissionTemplate(
        code="marketing",
        label="📢 Marketing",
        description="Xabar yuborish, promo-kod yaratish, so'rovnoma/viktorina tashkil qilish",
        permissions=(
            Permission.BROADCAST_SEND,
            Permission.PROMO_MANAGE,
            Permission.POLL_MANAGE,
        ),
    ),
    "full_access": PermissionTemplate(
        code="full_access",
        label="👑 To'liq huquq",
        description="Barcha ruxsatlar (main-admin darajasiga yaqin, lekin admin boshqaruvisiz)",
        permissions=tuple(Permission.all()),
    ),
}


def get_template(code: str) -> PermissionTemplate | None:
    return TEMPLATES.get(code)
