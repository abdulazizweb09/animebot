"""🎟 Promo-kod yaratish (#19) va 🎁 VIP sovg'a qilish (#17) — admin."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from config.enums import Permission, PromoCodeType
from container import Container
from filters.admin_filters import IsAdmin
from states.admin_states import GiftVipStates, PromoCreateStates

router = Router(name="admin_promo")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _require_permission(message: Message, container: Container) -> bool:
    allowed = await container.permission_service.has_permission(
        message.from_user.id, Permission.PROMO_MANAGE
    )
    if not allowed:
        await message.answer("🚫 Sizda bu amal uchun ruxsat yo'q.")
    return allowed


# ---------------------------------------------------------------------------
# #19 Admin Coupon Generator
# ---------------------------------------------------------------------------


@router.message(F.text == "🎟 Promo-kodlar")
async def promo_menu(message: Message, container: Container) -> None:
    if not await _require_permission(message, container):
        return

    active = await container.promo_service.list_active_codes()
    lines = ["🎟 Aktiv promo-kodlar:"] if active else ["🎟 Hozircha aktiv kod yo'q."]
    for p in active:
        lines.append(f"  • <code>{p.code}</code> — {p.type} {p.value} ({p.used_count}/{p.max_uses})")
    lines.append("\n➕ Yangi kod yaratish uchun: /newpromo")
    await message.answer("\n".join(lines))


@router.message(F.text == "/newpromo")
async def start_new_promo(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container):
        return
    rows = [
        [InlineKeyboardButton(text="💎 VIP kunlar", callback_data="promotype:vip_days")],
        [InlineKeyboardButton(text="💰 Tangalar", callback_data="promotype:coins")],
    ]
    await state.set_state(PromoCreateStates.waiting_type)
    await message.answer(
        "🎟 Promo-kod turini tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(PromoCreateStates.waiting_type, F.data.startswith("promotype:"))
async def promo_type_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    type_value = callback.data.split(":", 1)[1]
    await state.update_data(promo_type=type_value)
    await state.set_state(PromoCreateStates.waiting_value)
    label = "kunlar sonini" if type_value == "vip_days" else "tangalar sonini"
    await callback.message.answer(f"🔢 {label} kiriting (masalan: 30):")
    await callback.answer()


@router.message(PromoCreateStates.waiting_value, F.text)
async def promo_value_entered(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqam kiriting:")
        return
    await state.update_data(value=int(message.text.strip()))
    await state.set_state(PromoCreateStates.waiting_max_uses)
    await message.answer("👥 Nechta marta ishlatilishi mumkin? (masalan: 1, 10, 100):")


@router.message(PromoCreateStates.waiting_max_uses, F.text)
async def promo_max_uses_entered(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqam kiriting:")
        return
    await state.update_data(max_uses=int(message.text.strip()))
    await state.set_state(PromoCreateStates.waiting_expiry_days)
    await message.answer("📅 Necha kun amal qiladi? (cheksiz uchun /skip):")


@router.message(PromoCreateStates.waiting_expiry_days, F.text == "/skip")
async def promo_expiry_skipped(message: Message, state: FSMContext, container: Container) -> None:
    await _finish_promo_creation(message, state, container, expires_in_days=None)


@router.message(PromoCreateStates.waiting_expiry_days, F.text)
async def promo_expiry_entered(message: Message, state: FSMContext, container: Container) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqam kiriting yoki /skip bosing:")
        return
    await _finish_promo_creation(message, state, container, expires_in_days=int(message.text.strip()))


async def _finish_promo_creation(
    message: Message, state: FSMContext, container: Container, expires_in_days: int | None
) -> None:
    data = await state.get_data()
    await state.clear()

    promo = await container.promo_service.create_code(
        promo_type=PromoCodeType(data["promo_type"]),
        value=data["value"],
        created_by=message.from_user.id,
        max_uses=data["max_uses"],
        expires_in_days=expires_in_days,
    )
    await message.answer(
        f"✅ Promo-kod yaratildi:\n\n<code>{promo.code}</code>\n"
        f"Turi: {promo.type}, qiymati: {promo.value}, limit: {promo.max_uses} marta"
    )


# ---------------------------------------------------------------------------
# #17 Gift VIP
# ---------------------------------------------------------------------------


@router.message(F.text == "🎁 VIP sovg'a")
async def start_gift_vip(message: Message, state: FSMContext, container: Container) -> None:
    if not await _require_permission(message, container):
        return
    await state.set_state(GiftVipStates.waiting_user_id)
    await message.answer("🎁 VIP sovg'a qilinadigan foydalanuvchi ID sini kiriting:")


@router.message(GiftVipStates.waiting_user_id, F.text)
async def gift_vip_user_entered(message: Message, state: FSMContext, container: Container) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqamli ID kiriting:")
        return
    user_id = int(message.text.strip())
    user = await container.users.get_by_id(user_id)
    if user is None:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        await state.clear()
        return

    await state.update_data(gift_user_id=user_id)
    await state.set_state(GiftVipStates.waiting_days)
    await message.answer("📅 Necha kunlik VIP sovg'a qilamiz?")


@router.message(GiftVipStates.waiting_days, F.text)
async def gift_vip_days_entered(
    message: Message, state: FSMContext, container: Container
) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqam kiriting:")
        return

    data = await state.get_data()
    user_id = data["gift_user_id"]
    days = int(message.text.strip())
    await state.clear()

    await container.promo_service.gift_vip(message.from_user.id, user_id, days)
    await message.answer(f"✅ {user_id} foydalanuvchiga {days} kunlik VIP sovg'a qilindi.")

    try:
        await message.bot.send_message(
            user_id, f"🎁 Sizga admin tomonidan {days} kunlik VIP obuna sovg'a qilindi!"
        )
    except Exception:  # noqa: BLE001
        pass

    tier = await container.vip_service.get_tier(user_id)
    tier_badge = await container.achievement_service.award_vip_tier_badge(user_id, tier)
    if tier_badge:
        try:
            await message.bot.send_message(
                user_id,
                f"🌟 Tabriklaymiz! Siz endi <b>{tier.label}</b> darajasidasiz!\n"
                f"🏆 {tier_badge.label} — {tier_badge.description}",
            )
        except Exception:  # noqa: BLE001
            pass
