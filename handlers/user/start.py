"""``/start`` va unga bog'liq til tanlash / majburiy obuna oqimi.

Oqim:
    1. Foydalanuvchi ``/start`` yuboradi -> ``UserMiddleware`` uni DB'da
       yaratadi/yuklaydi.
    2. Agar yangi foydalanuvchi bo'lsa -> til tanlash klaviaturasi.
    3. Til tanlangandan so'ng (yoki eski foydalanuvchi uchun to'g'ridan-to'g'ri)
       -> majburiy obuna tekshiriladi.
    4. Obuna bo'lmagan kanallar bo'lsa -> obuna qilish klaviaturasi + "Tekshirish"
       tugmasi.
    5. Hammasi joyida bo'lsa -> asosiy menyu.
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.constants import CONSTANTS
from container import Container
from database.models.user import User
from keyboards.user.force_sub import force_sub_keyboard
from keyboards.user.language import language_keyboard
from keyboards.user.main_menu import main_menu_keyboard
from utils.i18n import t
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="user_start")


def _parse_shared_anime_code(start_param: str | None) -> str | None:
    if not start_param or not start_param.startswith("anime_"):
        return None
    return start_param[len("anime_"):].upper()


async def _show_shared_anime(message: Message, container: Container, db_user: User, code: str) -> None:
    """#Anime ulashish — deep-link orqali kelgan foydalanuvchiga to'g'ridan-
    to'g'ri anime kartochkasini ko'rsatadi."""

    from handlers.user.anime_detail import send_anime_card

    anime = await container.anime_service.get_detail(code)
    if anime is None:
        return

    await send_anime_card(message, container, db_user, anime)


async def _proceed_after_language(
    message: Message,
    bot: Bot,
    container: Container,
    db_user: User,
    state: FSMContext | None = None,
) -> None:
    """Til tanlangandan/tasdiqlangandan keyingi qadam: obuna tekshirish yoki menyu.

    MUHIM: VIP foydalanuvchilar majburiy obunadan OZOD — bu VIP xizmatning
    qo'shimcha afzalligi sifatida ishlaydi. Oddiy foydalanuvchilar uchun
    tekshiruv o'zgarishsiz davom etadi.
    """

    vip = await container.vips.get_active_for_user(db_user.user_id)
    if vip is None:
        ok, missing = await container.subscription_service.check_user_subscribed_all(
            bot, db_user.user_id
        )
        if not ok:
            await message.answer(
                t("force_sub_text", db_user.language),
                reply_markup=force_sub_keyboard(missing, db_user.language),
            )
            return

    await message.answer(
        t("welcome", db_user.language, name=db_user.full_name or "friend"),
    )
    await message.answer(
        t("main_menu", db_user.language),
        reply_markup=main_menu_keyboard(db_user.language),
    )

    if state is not None:
        data = await state.get_data()
        pending_code = data.get("pending_anime_code")
        if pending_code:
            await state.update_data(pending_anime_code=None)
            await _show_shared_anime(message, container, db_user, pending_code)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    bot: Bot,
    container: Container,
    db_user: User,
    is_new_user: bool,
    state: FSMContext,
) -> None:
    shared_code = _parse_shared_anime_code(command.args)
    if shared_code:
        await state.update_data(pending_anime_code=shared_code)

    if is_new_user:
        referrer_id = container.referral_service.parse_referrer_id(command.args)
        if referrer_id:
            registered = await container.referral_service.register_referral(
                referrer_id, db_user.user_id
            )
            if registered:
                logger.info("Referral orqali qo'shildi: referrer=%s new=%s", referrer_id, db_user.user_id)
                await container.analytics_service.log_event(
                    "referral_registered",
                    user_id=referrer_id,
                    meta={"referred_id": db_user.user_id},
                )

        await message.answer(
            t("choose_language", db_user.language),
            reply_markup=language_keyboard(),
        )
        return

    await _proceed_after_language(message, bot, container, db_user, state)


@router.callback_query(F.data.startswith(f"{CONSTANTS.CB_LANG}:"))
async def on_language_selected(
    callback: CallbackQuery, bot: Bot, container: Container, db_user: User, state: FSMContext
) -> None:
    language = callback.data.split(":", 1)[1]
    await container.user_service.set_language(db_user.user_id, language)
    db_user.language = language

    await callback.answer(t("language_selected", language))
    if callback.message:
        await callback.message.delete()
        await _proceed_after_language(callback.message, bot, container, db_user, state)


@router.callback_query(F.data == "force_sub_check")
async def on_force_sub_check(
    callback: CallbackQuery, bot: Bot, container: Container, db_user: User, state: FSMContext
) -> None:
    vip = await container.vips.get_active_for_user(db_user.user_id)
    if vip is None:
        ok, missing = await container.subscription_service.check_user_subscribed_all(
            bot, db_user.user_id
        )
        if not ok:
            await callback.answer(
                t("force_sub_not_subscribed", db_user.language), show_alert=True
            )
            return

    await callback.answer(t("force_sub_success", db_user.language))
    if callback.message:
        await callback.message.delete()
        await callback.message.answer(
            t("welcome", db_user.language, name=db_user.full_name or "friend"),
        )
        await callback.message.answer(
            t("main_menu", db_user.language),
            reply_markup=main_menu_keyboard(db_user.language),
        )

        data = await state.get_data()
        pending_code = data.get("pending_anime_code")
        if pending_code:
            await state.update_data(pending_anime_code=None)
            await _show_shared_anime(callback.message, container, db_user, pending_code)
