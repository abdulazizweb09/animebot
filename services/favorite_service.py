"""Sevimlilar bilan ishlash logikasi."""

from __future__ import annotations

import uuid

from database.models.interaction import Favorite
from database.repositories.interaction_repository import FavoriteRepository


class FavoriteService:
    def __init__(self, favorites: FavoriteRepository) -> None:
        self._favorites = favorites

    async def toggle(self, user_id: int, anime_code: str) -> bool:
        """Sevimliga qo'shadi/olib tashlaydi. Qaytaradi: endi sevimlimi (True/False)."""

        is_fav = await self._favorites.is_favorite(user_id, anime_code)
        if is_fav:
            await self._favorites.remove(user_id, anime_code)
            return False

        favorite = Favorite(id=str(uuid.uuid4()), user_id=user_id, anime_code=anime_code)
        await self._favorites.add(favorite)
        return True

    async def list_for_user(self, user_id: int) -> list[Favorite]:
        return await self._favorites.list_for_user(user_id)
