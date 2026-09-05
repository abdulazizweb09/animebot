"""Barcha handler routerlarini bitta joyda yig'adi."""

from aiogram import Router

from handlers.admin import admin_router
from handlers.user import user_router

main_router = Router(name="main")
# Admin router birinchi ulanadi — shunda admin buyruqlari user handlerlari
# bilan to'qnashmaydi (masalan, bitta xil matnli tugma bo'lsa).
main_router.include_router(admin_router)
main_router.include_router(user_router)

__all__ = ["main_router"]
