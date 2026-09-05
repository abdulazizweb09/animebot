"""``/admin`` — admin panelga kirish nuqtasi."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from container import Container
from database.models.user import User
from filters.admin_filters import IsAdmin
from keyboards.admin.main_menu import admin_menu_keyboard
from keyboards.user.main_menu import main_menu_keyboard

router = Router(name="admin_panel")
router.message.filter(IsAdmin())


@router.message(Command("admin"))
async def open_admin_panel(message: Message, container: Container) -> None:
    is_main = container.settings.is_main_admin(message.from_user.id)
    await message.answer(
        "🛠 Admin panelga xush kelibsiz.", reply_markup=admin_menu_keyboard(is_main)
    )


@router.message(F.text == "⬅️ Chiqish")
async def exit_admin_panel(message: Message, db_user: User) -> None:
    await message.answer("Admin paneldan chiqdingiz.", reply_markup=main_menu_keyboard(db_user.language))
