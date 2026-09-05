"""🔎 Foydalanuvchini qidirish/profil ko'rish (admin support vositasi).

Support so'rovlarga tez javob berish uchun — admin userning ID yoki
username'ini bilsa, uning to'liq holatini (VIP, ban, statistika) bir
zumda ko'radi.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from config.enums import Permission
from container import Container
from filters.admin_filters import IsAdmin

router = Router(name="admin_user_lookup")
router.message.filter(IsAdmin())


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.USER_LOOKUP
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


async def _render_profile(container: Container, user) -> str:
    vip = await container.vips.get_active_for_user(user.user_id)
    economy = await container.economy_service.get_profile(user.user_id)
    achievements = await container.achievement_service.list_for_user(user.user_id)
    history_count = len(await container.history.list_for_user(user.user_id, limit=10000))
    favorites_count = len(await container.favorites.list_for_user(user.user_id))

    vip_line = f"💎 VIP (tugash: {vip.expires_at[:10]})" if vip else "— VIP emas"
    ban_line = f"🚫 Bloklangan: {user.ban_reason or '-'}" if user.is_banned else "✅ Bloklanmagan"

    return (
        f"👤 <b>Foydalanuvchi profili</b>\n\n"
        f"ID: <code>{user.user_id}</code>\n"
        f"Username: @{user.username or '-'}\n"
        f"Ism: {user.full_name or '-'}\n"
        f"Til: {user.language}\n"
        f"Rol: {user.role}\n"
        f"{ban_line}\n"
        f"{vip_line}\n\n"
        f"✨ XP: {economy.xp} (daraja {economy.level})\n"
        f"💰 Tangalar: {economy.coins}\n"
        f"🏆 Yutuqlar: {len(achievements)}\n"
        f"🎞 Ko'rilgan qismlar: {economy.total_episodes_watched}\n"
        f"🕘 Tarix yozuvlari: {history_count}\n"
        f"❤️ Sevimlilar: {favorites_count}\n\n"
        f"📅 Ro'yxatdan o'tgan: {user.joined_at[:10]}\n"
        f"🕐 Oxirgi faollik: {(user.last_active_at or '-')[:16].replace('T', ' ')}"
    )


@router.message(F.text.startswith("/finduser "))
async def find_user(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    query = message.text.split(" ", 1)[1].strip()

    if query.isdigit():
        user = await container.users.get_by_id(int(query))
        results = [user] if user else []
    else:
        results = await container.users.search_by_username_or_id(query)

    if not results:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    if len(results) > 1:
        lines = ["🔎 Bir nechta natija topildi:\n"]
        for u in results[:10]:
            lines.append(f"• <code>{u.user_id}</code> — @{u.username or '-'} ({u.full_name or '-'})")
        lines.append("\nAniqroq qidirish uchun to'liq ID kiriting.")
        await message.answer("\n".join(lines))
        return

    text = await _render_profile(container, results[0])
    await message.answer(text)


@router.message(F.text.startswith("/grantxp "))
async def grant_xp(message: Message, container: Container) -> None:
    """Format: /grantxp <user_id> <miqdor> — foydalanuvchiga qo'lda XP berish."""

    if not await _require_permission(message, container):
        return

    parts = message.text.split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].lstrip("-").isdigit():
        await message.answer("⚠️ Format: /grantxp <user_id> <miqdor>")
        return

    user_id, amount = int(parts[1]), int(parts[2])
    user = await container.users.get_by_id(user_id)
    if user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    profile = await container.economy_service.add_xp(user_id, amount)
    await message.answer(f"✅ {user_id} ga {amount} XP berildi. Joriy XP: {profile.xp} (daraja {profile.level})")


@router.message(F.text.startswith("/grantcoins "))
async def grant_coins(message: Message, container: Container) -> None:
    """Format: /grantcoins <user_id> <miqdor> — foydalanuvchiga qo'lda tanga berish."""

    if not await _require_permission(message, container):
        return

    parts = message.text.split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].lstrip("-").isdigit():
        await message.answer("⚠️ Format: /grantcoins <user_id> <miqdor>")
        return

    user_id, amount = int(parts[1]), int(parts[2])
    user = await container.users.get_by_id(user_id)
    if user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    profile = await container.economy_service.add_coins(user_id, amount)
    await message.answer(f"✅ {user_id} ga {amount} tanga berildi. Joriy tanga: {profile.coins}")
