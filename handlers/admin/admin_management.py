"""👮 Adminlarni qo'shish/olib tashlash va 🔑 ruxsatlarni boshqarish (faqat main-admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from config.enums import Permission
from config.permission_templates import TEMPLATES, get_template
from container import Container
from filters.admin_filters import IsMainAdmin
from states.admin_states import AdminManageStates

router = Router(name="admin_management")
router.message.filter(IsMainAdmin())
router.callback_query.filter(IsMainAdmin())


@router.message(F.text == "👮 Adminlar")
async def list_admins_menu(message: Message, state: FSMContext, container: Container) -> None:
    admin_ids = await container.admin_service.list_admins()
    text_lines = ["👮 Runtime adminlar:"]
    text_lines += [f"• <code>{a}</code>" for a in admin_ids] or ["— (yo'q)"]
    text_lines.append(
        "\nYangi admin qo'shish uchun ID yuboring, olib tashlash uchun: /removeadmin [id]"
    )
    await message.answer("\n".join(text_lines))
    await state.set_state(AdminManageStates.waiting_new_admin_id)


@router.message(AdminManageStates.waiting_new_admin_id, F.text)
async def new_admin_id_entered(message: Message, state: FSMContext, container: Container) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqamli ID kiriting:")
        return
    admin_id = int(message.text.strip())
    added = await container.admin_service.add_admin(admin_id, message.from_user.id)
    await state.clear()
    await message.answer("✅ Admin qo'shildi." if added else "⚠️ Bu foydalanuvchi allaqachon admin.")


@router.message(F.text.startswith("/removeadmin "))
async def remove_admin_cmd(message: Message, container: Container) -> None:
    raw = message.text.split(" ", 1)[1].strip()
    if not raw.isdigit():
        await message.answer("⚠️ Raqamli ID kiriting.")
        return
    removed = await container.admin_service.remove_admin(int(raw), message.from_user.id)
    await message.answer("✅ Admin olib tashlandi." if removed else "❌ Topilmadi.")


@router.message(F.text == "🔑 Ruxsatlar")
async def start_permission_management(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminManageStates.waiting_permission_selection)
    await message.answer("🔑 Ruxsatlarini o'zgartirmoqchi bo'lgan admin ID sini kiriting:")


@router.message(AdminManageStates.waiting_permission_selection, F.text)
async def permission_admin_id_entered(
    message: Message, state: FSMContext, container: Container
) -> None:
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Raqamli ID kiriting:")
        return
    admin_id = int(message.text.strip())
    await state.update_data(perm_admin_id=admin_id)

    template_rows = [
        [InlineKeyboardButton(text=tpl.label, callback_data=f"permtpl:{admin_id}:{code}")]
        for code, tpl in TEMPLATES.items()
    ]
    template_rows.append(
        [InlineKeyboardButton(text="✏️ Qo'lda tanlash", callback_data=f"permmanual:{admin_id}")]
    )

    lines = ["🔑 Tayyor shablonlardan birini tanlang yoki qo'lda belgilang:\n"]
    for tpl in TEMPLATES.values():
        lines.append(f"{tpl.label} — {tpl.description}")

    await message.answer(
        "\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=template_rows)
    )


@router.callback_query(F.data.startswith("permtpl:"))
async def apply_permission_template(callback: CallbackQuery, container: Container) -> None:
    _, admin_id_raw, template_code = callback.data.split(":")
    admin_id = int(admin_id_raw)

    template = get_template(template_code)
    if template is None:
        await callback.answer("Shablon topilmadi.", show_alert=True)
        return

    await container.permission_service.set_permissions(admin_id, list(template.permissions))
    await callback.message.edit_text(
        f"✅ Admin {admin_id} uchun '{template.label}' shabloni qo'llanildi.\n\n"
        f"Ruxsatlar: {', '.join(p.value for p in template.permissions)}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("permmanual:"))
async def show_manual_permission_toggle(callback: CallbackQuery, container: Container) -> None:
    admin_id = int(callback.data.split(":", 1)[1])
    current = await container.permission_service.get_permissions(admin_id)

    rows = []
    for perm in Permission.all():
        mark = "✅" if perm.value in current else "▫️"
        rows.append(
            [InlineKeyboardButton(text=f"{mark} {perm.value}", callback_data=f"permtoggle:{admin_id}:{perm.value}")]
        )
    rows.append([InlineKeyboardButton(text="✅ Tayyor", callback_data=f"permdone:{admin_id}")])

    await callback.message.edit_text(
        f"🔑 Admin {admin_id} uchun ruxsatlar (bosib yoqing/o'chiring):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("permtoggle:"))
async def toggle_permission(callback: CallbackQuery, container: Container) -> None:
    _, admin_id_raw, perm_value = callback.data.split(":")
    admin_id = int(admin_id_raw)
    permission = Permission(perm_value)

    current = await container.permission_service.get_permissions(admin_id)
    if perm_value in current:
        await container.permission_service.revoke(admin_id, permission)
    else:
        await container.permission_service.grant(admin_id, permission)

    updated = await container.permission_service.get_permissions(admin_id)
    rows = []
    for perm in Permission.all():
        mark = "✅" if perm.value in updated else "▫️"
        rows.append(
            [InlineKeyboardButton(text=f"{mark} {perm.value}", callback_data=f"permtoggle:{admin_id}:{perm.value}")]
        )
    rows.append([InlineKeyboardButton(text="✅ Tayyor", callback_data=f"permdone:{admin_id}")])
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("permdone:"))
async def finish_permission_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("✅ Ruxsatlar saqlandi.")
    await callback.answer()
