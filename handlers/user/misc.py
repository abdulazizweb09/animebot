"""Mayda umumiy handlerlar (masalan, "noop" tugmasi)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="user_misc")


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
