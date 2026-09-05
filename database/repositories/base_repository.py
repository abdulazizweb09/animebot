"""Barcha "list" turidagi JSON fayllar uchun umumiy CRUD repository.

Har bir aniq repository (``UserRepository``, ``AnimeRepository``, ...) shu
klassdan meros oladi va faqat domenga xos qo'shimcha metodlarni qo'shadi.
Bu takrorlanadigan CRUD kodni bitta joyda ushlab turadi (DRY).
"""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

from database.json_manager import JsonManager
from utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """``filename`` dagi ro'yxatni ``id_field`` bo'yicha boshqaruvchi repository.

    ``model_cls`` — ``to_dict()`` / ``from_dict()`` metodlariga ega dataclass.
    """

    def __init__(
        self,
        manager: JsonManager,
        filename: str,
        model_cls: type[T],
        id_field: str = "id",
    ) -> None:
        self._manager = manager
        self._filename = filename
        self._model_cls = model_cls
        self._id_field = id_field

    # ------------------------------------------------------------------

    async def all(self, include_deleted: bool = False, use_cache: bool = True) -> list[T]:
        raw = await self._manager.read(self._filename, default=[], use_cache=use_cache)
        items = [self._model_cls.from_dict(item) for item in raw]
        if not include_deleted:
            items = [i for i in items if not getattr(i, "is_deleted", False)]
        return items

    async def get(self, item_id: Any, use_cache: bool = True) -> T | None:
        raw = await self._manager.read(self._filename, default=[], use_cache=use_cache)
        for item in raw:
            if item.get(self._id_field) == item_id:
                return self._model_cls.from_dict(item)
        return None

    async def find_one(self, predicate: Callable[[dict[str, Any]], bool]) -> T | None:
        raw = await self._manager.read(self._filename, default=[])
        for item in raw:
            if predicate(item):
                return self._model_cls.from_dict(item)
        return None

    async def find_all(self, predicate: Callable[[dict[str, Any]], bool]) -> list[T]:
        raw = await self._manager.read(self._filename, default=[])
        return [self._model_cls.from_dict(item) for item in raw if predicate(item)]

    async def exists(self, item_id: Any, use_cache: bool = True) -> bool:
        return await self.get(item_id, use_cache=use_cache) is not None

    async def add(self, item: T) -> T:
        def _updater(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
            data.append(item.to_dict())
            return data

        await self._manager.update(self._filename, _updater, default=[])
        return item

    async def add_if_absent(self, item: T) -> tuple[T | None, bool]:
        """``add()`` bilan bir xil, lekin ``id_field`` bo'yicha noyoblikni
        BITTA atomik lock ostida tekshiradi va qo'shadi.

        Bu "tekshir keyin qo'sh" (check-then-add) naqshidagi race-condition'ni
        yo'q qiladi — masalan, ikkita admin bir vaqtda bir xil anime kodini
        yoki promo-kodni yaratmoqchi bo'lsa, faqat BITTASI muvaffaqiyatli
        bo'ladi (xuddi ``EpisodeRepository.add_with_auto_number()`` dagi
        kabi tamoyil).

        Qaytaradi: ``(item, True)`` — muvaffaqiyatli qo'shildi;
        ``(None, False)`` — bunday ID allaqachon mavjud, hech narsa
        o'zgartirilmadi.
        """

        result_holder: dict[str, bool] = {"added": False}

        def _updater(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
            item_dict = item.to_dict()
            item_id = item_dict[self._id_field]
            for entry in data:
                if entry.get(self._id_field) == item_id:
                    result_holder["added"] = False
                    return data
            data.append(item_dict)
            result_holder["added"] = True
            return data

        await self._manager.update(self._filename, _updater, default=[])
        if result_holder["added"]:
            return item, True
        return None, False

    async def update(self, item_id: Any, changes: dict[str, Any]) -> T | None:
        result: dict[str, Any] | None = None

        def _updater(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
            nonlocal result
            for entry in data:
                if entry.get(self._id_field) == item_id:
                    entry.update(changes)
                    result = entry
                    break
            return data

        await self._manager.update(self._filename, _updater, default=[])
        return self._model_cls.from_dict(result) if result else None

    async def replace(self, item: T) -> T:
        """Butun yozuvni ``item``ning ``id_field`` qiymati bo'yicha almashtiradi."""

        item_dict = item.to_dict()
        item_id = item_dict[self._id_field]

        def _updater(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
            for i, entry in enumerate(data):
                if entry.get(self._id_field) == item_id:
                    data[i] = item_dict
                    return data
            data.append(item_dict)
            return data

        await self._manager.update(self._filename, _updater, default=[])
        return item

    async def soft_delete(self, item_id: Any) -> bool:
        return await self.update(item_id, {"is_deleted": True}) is not None

    async def hard_delete(self, item_id: Any) -> bool:
        removed = False

        def _updater(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
            nonlocal removed
            new_data = [d for d in data if d.get(self._id_field) != item_id]
            removed = len(new_data) != len(data)
            return new_data

        await self._manager.update(self._filename, _updater, default=[])
        return removed

    async def count(self, include_deleted: bool = False) -> int:
        items = await self.all(include_deleted=include_deleted)
        return len(items)
