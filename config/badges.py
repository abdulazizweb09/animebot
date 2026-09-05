"""Achievement/badge ta'riflari — markazlashtirilgan ro'yxat (#12).

Yangi badge qo'shish uchun shu yerga bitta yozuv qo'shish kifoya —
AchievementService avtomatik ravishda shartlarni tekshiradi.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BadgeDefinition:
    code: str
    label: str
    description: str


EPISODE_MILESTONES: dict[int, BadgeDefinition] = {
    100: BadgeDefinition("episodes_100", "🥉 100 qism", "100 ta epizod ko'rildi"),
    500: BadgeDefinition("episodes_500", "🥈 500 qism", "500 ta epizod ko'rildi"),
    1000: BadgeDefinition("episodes_1000", "🥇 1000 qism", "1000 ta epizod ko'rildi"),
}

VIP_BADGE = BadgeDefinition("vip_member", "💎 VIP", "VIP obunaga ega bo'lindi")
VIP_SILVER_BADGE = BadgeDefinition(
    "vip_silver", "🥈 Silver VIP", "90+ kunlik VIP loyallik darajasiga yetildi"
)
VIP_GOLD_BADGE = BadgeDefinition(
    "vip_gold", "🥇 Gold VIP", "365+ kunlik VIP loyallik darajasiga yetildi"
)
AI_USER_BADGE = BadgeDefinition("ai_user", "🤖 AI User", "AI yordamchidan birinchi marta foydalanildi")
EARLY_BIRD_BADGE = BadgeDefinition("early_bird", "🐣 Early Bird", "Botning birinchi foydalanuvchilaridan biri")

ALL_BADGES: dict[str, BadgeDefinition] = {
    **{b.code: b for b in EPISODE_MILESTONES.values()},
    VIP_BADGE.code: VIP_BADGE,
    VIP_SILVER_BADGE.code: VIP_SILVER_BADGE,
    VIP_GOLD_BADGE.code: VIP_GOLD_BADGE,
    AI_USER_BADGE.code: AI_USER_BADGE,
    EARLY_BIRD_BADGE.code: EARLY_BIRD_BADGE,
}
