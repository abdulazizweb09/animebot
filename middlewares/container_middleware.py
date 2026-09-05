"""Har bir update uchun ``container`` ni ``data`` ichiga qo'shadigan middleware.

Bundan keyin har qanday handler ``async def handler(message, container: Container)``
sifatida DI konteynerni to'g'ridan-to'g'ri parametr sifatida olishi mumkin
(aiogram avtomatik ``data`` dict'idan mos nomdagi kalitni topib beradi).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from container import Container, get_container


class ContainerMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._container: Container = get_container()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["container"] = self._container
        return await handler(event, data)
