# """🤖 AI Yordamchi (Gemini asosida) — foydalanuvchi chat oqimi.

# MUHIM: AI xizmatlari FAQAT VIP foydalanuvchilar uchun ochiq — bu VIP
# obunaning asosiy afzalliklaridan biri sifatida ishlaydi.
# """

# from __future__ import annotations

# from aiogram import F, Router
# from aiogram.fsm.context import FSMContext
# from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

# from container import Container
# from database.models.user import User
# from states.user_states import AIChatStates
# from utils.exceptions import AIServiceError, RateLimitExceededError
# from utils.i18n import all_variants
# from utils.logger import get_logger

# logger = get_logger(__name__)
# router = Router(name="user_ai")

# _EXIT_TEXT = "🔚 Chatni tugatish"
# _CLEAR_TEXT = "🧹 Suhbatni tozalash"

# _VIP_ONLY_TEXT = (
#     "🔒 AI Yordamchi faqat VIP foydalanuvchilar uchun mavjud.\n\n"
#     "💎 VIP bo'lib, AI Yordamchi, ovozli/rasm orqali qidiruv va boshqa "
#     "eksklyuziv imkoniyatlardan foydalaning!"
# )


# def _ai_chat_keyboard() -> ReplyKeyboardMarkup:
#     return ReplyKeyboardMarkup(
#         keyboard=[[KeyboardButton(text=_CLEAR_TEXT)], [KeyboardButton(text=_EXIT_TEXT)]],
#         resize_keyboard=True,
#     )


# async def require_vip_for_ai(message: Message, container: Container, db_user: User) -> bool:
#     """AI-bog'liq xizmatlar (chat, ovozli/rasm qidiruv) uchun umumiy VIP
#     tekshiruvi. ``True`` — ruxsat bor, ``False`` — yo'q (xabar allaqachon
#     yuborilgan).
#     """

#     if db_user.is_admin:
#         return True

#     vip = await container.vips.get_active_for_user(db_user.user_id)
#     if vip is None:
#         await message.answer(_VIP_ONLY_TEXT)
#         return False
#     return True


# @router.message(F.text.in_(all_variants("btn_ai")))
# async def start_ai_chat(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         return

#     await state.set_state(AIChatStates.chatting)
#     await message.answer(
#         "🤖 Salom! Men animeAI — anime yordamchingizman. Nima haqida gaplashamiz?",
#         reply_markup=_ai_chat_keyboard(),
#     )


# @router.message(AIChatStates.chatting, F.text == _CLEAR_TEXT)
# async def clear_ai_chat(message: Message, container: Container, db_user: User) -> None:
#     await container.ai_service.clear_history(db_user.user_id)
#     await message.answer("🧹 Suhbat tarixi tozalandi. Yangi mavzudan boshlashingiz mumkin.")


# @router.message(AIChatStates.chatting, F.text == _EXIT_TEXT)
# async def exit_ai_chat(message: Message, state: FSMContext, db_user: User) -> None:
#     from keyboards.user.main_menu import main_menu_keyboard

#     await state.clear()
#     await message.answer("👋 Chat tugatildi.", reply_markup=main_menu_keyboard(db_user.language))


# @router.message(AIChatStates.chatting, F.text)
# async def ai_chat_message(
#     message: Message, state: FSMContext, container: Container, db_user: User
# ) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         await state.clear()
#         return

#     await message.bot.send_chat_action(message.chat.id, "typing")
#     await message.bot.identify_anime_from_image(message.chat.id, "typing")
#     try:
#         reply = await container.ai_service.ask(db_user.user_id, message.text)
#     except RateLimitExceededError:
#         await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
#         return
#     except AIServiceError as exc:
#         logger.error("AI xatosi: %s", exc)
#         await message.answer("⚠️ AI hozircha javob berolmadi. Birozdan so'ng qayta urinib ko'ring.")
#         return

#     await message.answer(reply)
#     await container.analytics_service.log_event("ai_request", user_id=db_user.user_id)

#     awarded = await container.achievement_service.award_ai_user_badge(db_user.user_id)
#     if awarded:
#         from config.badges import AI_USER_BADGE

#         await message.answer(
#             f"🏆 Yangi yutuq: <b>{AI_USER_BADGE.label}</b>\n{AI_USER_BADGE.description}"
#         )









# """🤖 AI Yordamchi (Gemini asosida) — foydalanuvchi chat oqimi.

# MUHIM: AI xizmatlari FAQAT VIP foydalanuvchilar uchun ochiq — bu VIP
# obunaning asosiy afzalliklaridan biri sifatida ishlaydi.
# """

# from __future__ import annotations

# from aiogram import F, Router
# from aiogram.fsm.context import FSMContext
# from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

# from container import Container
# from database.models.user import User
# from states.user_states import AIChatStates
# from utils.exceptions import (
#     AIResponseEmptyError,
#     AIServiceError,
#     RateLimitExceededError,
# )
# from utils.i18n import all_variants
# from utils.logger import get_logger

# logger = get_logger(__name__)
# router = Router(name="user_ai")

# _EXIT_TEXT = "🔚 Chatni tugatish"
# _CLEAR_TEXT = "🧹 Suhbatni tozalash"

# _VIP_ONLY_TEXT = (
#     "🔒 AI Yordamchi faqat VIP foydalanuvchilar uchun mavjud.\n\n"
#     "💎 VIP bo'lib, AI Yordamchi, ovozli/rasm orqali qidiruv va boshqa "
#     "eksklyuziv imkoniyatlardan foydalaning!"
# )

# # Rasm/audio/video hajmi uchun xavfsizlik chegarasi (Telegram/Gemini
# # limitlariga mos, kerak bo'lsa constants.py'ga ko'chiring).
# _MAX_MEDIA_BYTES = 20 * 1024 * 1024  # 20 MB


# def _ai_chat_keyboard() -> ReplyKeyboardMarkup:
#     return ReplyKeyboardMarkup(
#         keyboard=[[KeyboardButton(text=_CLEAR_TEXT)], [KeyboardButton(text=_EXIT_TEXT)]],
#         resize_keyboard=True,
#     )


# async def require_vip_for_ai(message: Message, container: Container, db_user: User) -> bool:
#     """AI-bog'liq xizmatlar (chat, ovozli/rasm qidiruv) uchun umumiy VIP
#     tekshiruvi. ``True`` — ruxsat bor, ``False`` — yo'q (xabar allaqachon
#     yuborilgan).
#     """

#     if db_user.is_admin:
#         return True

#     vip = await container.vips.get_active_for_user(db_user.user_id)
#     if vip is None:
#         await message.answer(_VIP_ONLY_TEXT)
#         return False
#     return True


# async def _download_file_bytes(message: Message, file_id: str) -> bytes:
#     """Telegram fayl ID orqali baytlarni yuklab oladi."""

#     file = await message.bot.get_file(file_id)
#     buffer = await message.bot.download_file(file.file_path)
#     return buffer.read()


# @router.message(F.text.in_(all_variants("btn_ai")))
# async def start_ai_chat(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         return

#     await state.set_state(AIChatStates.chatting)
#     await message.answer(
#         "🤖 Salom! Men animeAI — anime yordamchingizman. Nima haqida gaplashamiz?",
#         reply_markup=_ai_chat_keyboard(),
#     )


# @router.message(AIChatStates.chatting, F.text == _CLEAR_TEXT)
# async def clear_ai_chat(message: Message, container: Container, db_user: User) -> None:
#     await container.ai_service.clear_history(db_user.user_id)
#     await message.answer("🧹 Suhbat tarixi tozalandi. Yangi mavzudan boshlashingiz mumkin.")


# @router.message(AIChatStates.chatting, F.text == _EXIT_TEXT)
# async def exit_ai_chat(message: Message, state: FSMContext, db_user: User) -> None:
#     from keyboards.user.main_menu import main_menu_keyboard

#     await state.clear()
#     await message.answer("👋 Chat tugatildi.", reply_markup=main_menu_keyboard(db_user.language))


# @router.message(AIChatStates.chatting, F.text)
# async def ai_chat_message(
#     message: Message, state: FSMContext, container: Container, db_user: User
# ) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         await state.clear()
#         return

#     await message.bot.send_chat_action(message.chat.id, "typing")
#     # ⚠️ Avval shu yerda noto'g'ri qator bor edi:
#     #   await message.bot.identify_anime_from_image(message.chat.id, "typing")
#     # Bu `Bot` obyektida mavjud bo'lmagan metodni chaqirib, har bir matnli
#     # xabarda AttributeError bilan handlerni ishdan chiqarayotgan edi.
#     # Shuning uchun olib tashlandi.

#     try:
#         reply = await container.ai_service.ask(db_user.user_id, message.text)
#     except RateLimitExceededError:
#         await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
#         return
#     except AIServiceError as exc:
#         logger.error("AI xatosi: %s", exc, exc_info=True)
#         await message.answer("⚠️ AI hozircha javob berolmadi. Birozdan so'ng qayta urinib ko'ring.")
#         return

#     await message.answer(reply)
#     await container.analytics_service.log_event("ai_request", user_id=db_user.user_id)

#     awarded = await container.achievement_service.award_ai_user_badge(db_user.user_id)
#     if awarded:
#         from config.badges import AI_USER_BADGE

#         await message.answer(
#             f"🏆 Yangi yutuq: <b>{AI_USER_BADGE.label}</b>\n{AI_USER_BADGE.description}"
#         )


# # --------------------------------------------------------------------------
# # Rasm orqali anime qidirish
# # --------------------------------------------------------------------------
# @router.message(AIChatStates.chatting, F.photo)
# async def ai_chat_photo(
#     message: Message, state: FSMContext, container: Container, db_user: User
# ) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         await state.clear()
#         return

#     photo = message.photo[-1]  # eng yuqori sifatli versiya
#     if photo.file_size and photo.file_size > _MAX_MEDIA_BYTES:
#         await message.answer("⚠️ Rasm hajmi juda katta. Kichikroq rasm yuboring.")
#         return

#     await message.bot.send_chat_action(message.chat.id, "typing")

#     try:
#         image_bytes = await _download_file_bytes(message, photo.file_id)
#         anime_name = await container.gemini_client.identify_anime_from_image(
#             image_bytes=image_bytes,
#             mime_type="image/jpeg",
#         )
#     except RateLimitExceededError:
#         await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
#         return
#     except AIResponseEmptyError:
#         await message.answer("🤔 Rasmdan anime nomini aniqlay olmadim. Boshqa rasm yuborib ko'ring.")
#         return
#     except AIServiceError as exc:
#         logger.error("AI rasm xatosi: %s", exc, exc_info=True)
#         await message.answer("⚠️ Rasmni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
#         return

#     # Agar rasmga caption (matn) ham qo'shilgan bo'lsa, uni ham hisobga olamiz
#     caption = message.caption
#     if caption:
#         try:
#             reply = await container.ai_service.ask(
#                 db_user.user_id,
#                 f"Rasmda '{anime_name}' anime aniqlandi. Foydalanuvchi savoli: {caption}",
#             )
#             await message.answer(reply)
#             return
#         except (RateLimitExceededError, AIServiceError):
#             pass  # pastdagi oddiy javobga tushib qolamiz

#     await message.answer(f"🎬 Bu anime shunga o'xshaydi: <b>{anime_name}</b>")
#     await container.analytics_service.log_event("ai_photo_request", user_id=db_user.user_id)


# # --------------------------------------------------------------------------
# # Ovozli xabar (voice) orqali anime qidirish
# # --------------------------------------------------------------------------
# @router.message(AIChatStates.chatting, F.voice)
# async def ai_chat_voice(
#     message: Message, state: FSMContext, container: Container, db_user: User
# ) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         await state.clear()
#         return

#     if message.voice.file_size and message.voice.file_size > _MAX_MEDIA_BYTES:
#         await message.answer("⚠️ Audio hajmi juda katta.")
#         return

#     await message.bot.send_chat_action(message.chat.id, "typing")

#     try:
#         audio_bytes = await _download_file_bytes(message, message.voice.file_id)
#         anime_name = await container.gemini_client.transcribe_audio(
#             audio_bytes=audio_bytes,
#             mime_type="audio/ogg",
#         )
#     except RateLimitExceededError:
#         await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
#         return
#     except AIResponseEmptyError:
#         await message.answer("🤔 Ovozdan anime nomini aniqlay olmadim.")
#         return
#     except AIServiceError as exc:
#         logger.error("AI audio xatosi: %s", exc, exc_info=True)
#         await message.answer("⚠️ Ovozni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
#         return

#     await message.answer(f"🎬 Siz shu haqda so'ragandirsiz: <b>{anime_name}</b>")
#     await container.analytics_service.log_event("ai_voice_request", user_id=db_user.user_id)


# # --------------------------------------------------------------------------
# # Audio fayl (voice emas, musiqa/fayl sifatida yuborilgan)
# # --------------------------------------------------------------------------
# @router.message(AIChatStates.chatting, F.audio)
# async def ai_chat_audio_file(
#     message: Message, state: FSMContext, container: Container, db_user: User
# ) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         await state.clear()
#         return

#     if message.audio.file_size and message.audio.file_size > _MAX_MEDIA_BYTES:
#         await message.answer("⚠️ Audio hajmi juda katta.")
#         return

#     await message.bot.send_chat_action(message.chat.id, "typing")

#     try:
#         audio_bytes = await _download_file_bytes(message, message.audio.file_id)
#         anime_name = await container.gemini_client.transcribe_audio(
#             audio_bytes=audio_bytes,
#             mime_type=message.audio.mime_type or "audio/mpeg",
#         )
#     except RateLimitExceededError:
#         await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
#         return
#     except AIResponseEmptyError:
#         await message.answer("🤔 Audio'dan anime nomini aniqlay olmadim.")
#         return
#     except AIServiceError as exc:
#         logger.error("AI audio-fayl xatosi: %s", exc, exc_info=True)
#         await message.answer("⚠️ Audio-ni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
#         return

#     await message.answer(f"🎬 Siz shu haqda so'ragandirsiz: <b>{anime_name}</b>")
#     await container.analytics_service.log_event("ai_audio_request", user_id=db_user.user_id)


# # --------------------------------------------------------------------------
# # Video orqali anime qidirish
# # --------------------------------------------------------------------------
# @router.message(AIChatStates.chatting, F.video)
# async def ai_chat_video(
#     message: Message, state: FSMContext, container: Container, db_user: User
# ) -> None:
#     if not await require_vip_for_ai(message, container, db_user):
#         await state.clear()
#         return

#     if message.video.file_size and message.video.file_size > _MAX_MEDIA_BYTES:
#         await message.answer("⚠️ Video hajmi juda katta.")
#         return

#     await message.bot.send_chat_action(message.chat.id, "typing")

#     try:
#         video_bytes = await _download_file_bytes(message, message.video.file_id)
#         anime_name = await container.gemini_client.identify_anime_from_video(
#             video_bytes=video_bytes,
#             mime_type=message.video.mime_type or "video/mp4",
#         )
#     except RateLimitExceededError:
#         await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
#         return
#     except AIResponseEmptyError:
#         await message.answer("🤔 Videodan anime nomini aniqlay olmadim.")
#         return
#     except AIServiceError as exc:
#         logger.error("AI video xatosi: %s", exc, exc_info=True)
#         await message.answer("⚠️ Videoni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
#         return

#     await message.answer(f"🎬 Bu anime shunga o'xshaydi: <b>{anime_name}</b>")
#     await container.analytics_service.log_event("ai_video_request", user_id=db_user.user_id)










"""🤖 AI Yordamchi (Gemini asosida) — foydalanuvchi chat oqimi.

MUHIM: AI xizmatlari FAQAT VIP foydalanuvchilar uchun ochiq — bu VIP
obunaning asosiy afzalliklaridan biri sifatida ishlaydi.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from container import Container
from database.models.user import User
from states.user_states import AIChatStates
from utils.exceptions import (
    AIResponseEmptyError,
    AIServiceError,
    RateLimitExceededError,
)
from utils.i18n import all_variants
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="user_ai")

_EXIT_TEXT = "🔚 Chatni tugatish"
_CLEAR_TEXT = "🧹 Suhbatni tozalash"

_VIP_ONLY_TEXT = (
    "🔒 AI Yordamchi faqat VIP foydalanuvchilar uchun mavjud.\n\n"
    "💎 VIP bo'lib, AI Yordamchi, ovozli/rasm orqali qidiruv va boshqa "
    "eksklyuziv imkoniyatlardan foydalaning!"
)

# Rasm/audio/video hajmi uchun xavfsizlik chegarasi (Telegram/Gemini
# limitlariga mos, kerak bo'lsa constants.py'ga ko'chiring).
_MAX_MEDIA_BYTES = 20 * 1024 * 1024  # 20 MB

# "AI o'ylayapti" stikeri. Bu ID'ni o'zgartiring: botga istalgan stikerni
# yuboring, keyin message.sticker.file_id orqali uni oling.
_THINKING_STICKER_ID = "CAACAgIAAxkBAAER2bBqm7Ofp_-UYQlxAnvza-7k9nSsFQACW1wBAAFji0YMrLK2QXamXBs9BA"


async def _send_thinking(message: Message) -> Message | None:
    """AI javob tayyorlayotganini bildiruvchi stikerni yuboradi.

    Xato bo'lsa ham (masalan stiker file_id noto'g'ri bo'lsa) butun
    handlerni ishdan chiqarmasligi uchun try/except bilan o'raladi —
    stiker ixtiyoriy narsa, asosiy funksionallik unga bog'liq bo'lmasligi
    kerak.
    """

    try:
        return await message.answer_sticker(_THINKING_STICKER_ID)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Thinking stikerini yuborib bo'lmadi: %s", exc)
        return None


async def _delete_thinking(thinking_msg: Message | None) -> None:
    """Yuborilgan 'o'ylayapman' stikerini o'chiradi."""

    if thinking_msg is None:
        return
    try:
        await thinking_msg.delete()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Thinking stikerini o'chirib bo'lmadi: %s", exc)


def _ai_chat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_CLEAR_TEXT)], [KeyboardButton(text=_EXIT_TEXT)]],
        resize_keyboard=True,
    )


async def require_vip_for_ai(message: Message, container: Container, db_user: User) -> bool:
    """AI-bog'liq xizmatlar (chat, ovozli/rasm qidiruv) uchun umumiy VIP
    tekshiruvi. ``True`` — ruxsat bor, ``False`` — yo'q (xabar allaqachon
    yuborilgan).
    """

    if db_user.is_admin:
        return True

    vip = await container.vips.get_active_for_user(db_user.user_id)
    if vip is None:
        await message.answer(_VIP_ONLY_TEXT)
        return False
    return True


async def _download_file_bytes(message: Message, file_id: str) -> bytes:
    """Telegram fayl ID orqali baytlarni yuklab oladi."""

    file = await message.bot.get_file(file_id)
    buffer = await message.bot.download_file(file.file_path)
    return buffer.read()


@router.message(F.text.in_(all_variants("btn_ai")))
async def start_ai_chat(message: Message, state: FSMContext, container: Container, db_user: User) -> None:
    if not await require_vip_for_ai(message, container, db_user):
        return

    await state.set_state(AIChatStates.chatting)
    await message.answer(
        "🤖 Salom! Men animeAI — anime yordamchingizman. Nima haqida gaplashamiz?",
        reply_markup=_ai_chat_keyboard(),
    )


@router.message(AIChatStates.chatting, F.text == _CLEAR_TEXT)
async def clear_ai_chat(message: Message, container: Container, db_user: User) -> None:
    await container.ai_service.clear_history(db_user.user_id)
    await message.answer("🧹 Suhbat tarixi tozalandi. Yangi mavzudan boshlashingiz mumkin.")


@router.message(AIChatStates.chatting, F.text == _EXIT_TEXT)
async def exit_ai_chat(message: Message, state: FSMContext, db_user: User) -> None:
    from keyboards.user.main_menu import main_menu_keyboard

    await state.clear()
    await message.answer("👋 Chat tugatildi.", reply_markup=main_menu_keyboard(db_user.language))


@router.message(AIChatStates.chatting, F.text)
async def ai_chat_message(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    if not await require_vip_for_ai(message, container, db_user):
        await state.clear()
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await _send_thinking(message)

    try:
        reply = await container.ai_service.ask(db_user.user_id, message.text)
    except RateLimitExceededError:
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
        return
    except AIServiceError as exc:
        logger.error("AI xatosi: %s", exc, exc_info=True)
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ AI hozircha javob berolmadi. Birozdan so'ng qayta urinib ko'ring.")
        return

    await _delete_thinking(thinking_msg)
    await message.answer(reply)
    await container.analytics_service.log_event("ai_request", user_id=db_user.user_id)

    awarded = await container.achievement_service.award_ai_user_badge(db_user.user_id)
    if awarded:
        from config.badges import AI_USER_BADGE

        await message.answer(
            f"🏆 Yangi yutuq: <b>{AI_USER_BADGE.label}</b>\n{AI_USER_BADGE.description}"
        )


# --------------------------------------------------------------------------
# Rasm orqali anime qidirish
# --------------------------------------------------------------------------
@router.message(AIChatStates.chatting, F.photo)
async def ai_chat_photo(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    if not await require_vip_for_ai(message, container, db_user):
        await state.clear()
        return

    photo = message.photo[-1]  # eng yuqori sifatli versiya
    if photo.file_size and photo.file_size > _MAX_MEDIA_BYTES:
        await message.answer("⚠️ Rasm hajmi juda katta. Kichikroq rasm yuboring.")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await _send_thinking(message)

    try:
        image_bytes = await _download_file_bytes(message, photo.file_id)
        anime_name = await container.gemini_client.identify_anime_from_image(
            image_bytes=image_bytes,
            mime_type="image/jpeg",
        )
    except RateLimitExceededError:
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
        return
    except AIResponseEmptyError:
        await _delete_thinking(thinking_msg)
        await message.answer("🤔 Rasmdan anime nomini aniqlay olmadim. Boshqa rasm yuborib ko'ring.")
        return
    except AIServiceError as exc:
        logger.error("AI rasm xatosi: %s", exc, exc_info=True)
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Rasmni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
        return

    # Agar rasmga caption (matn) ham qo'shilgan bo'lsa, uni ham hisobga olamiz
    caption = message.caption
    if caption:
        try:
            reply = await container.ai_service.ask(
                db_user.user_id,
                f"Rasmda '{anime_name}' anime aniqlandi. Foydalanuvchi savoli: {caption}",
            )
            await _delete_thinking(thinking_msg)
            await message.answer(reply)
            return
        except (RateLimitExceededError, AIServiceError):
            pass  # pastdagi oddiy javobga tushib qolamiz

    await _delete_thinking(thinking_msg)
    await message.answer(f"🎬 Bu anime shunga o'xshaydi: <b>{anime_name}</b>")
    await container.analytics_service.log_event("ai_photo_request", user_id=db_user.user_id)


# --------------------------------------------------------------------------
# Ovozli xabar (voice) orqali anime qidirish
# --------------------------------------------------------------------------
@router.message(AIChatStates.chatting, F.voice)
async def ai_chat_voice(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    if not await require_vip_for_ai(message, container, db_user):
        await state.clear()
        return

    if message.voice.file_size and message.voice.file_size > _MAX_MEDIA_BYTES:
        await message.answer("⚠️ Audio hajmi juda katta.")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await _send_thinking(message)

    try:
        audio_bytes = await _download_file_bytes(message, message.voice.file_id)
        anime_name = await container.gemini_client.transcribe_audio(
            audio_bytes=audio_bytes,
            mime_type="audio/ogg",
        )
    except RateLimitExceededError:
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
        return
    except AIResponseEmptyError:
        await _delete_thinking(thinking_msg)
        await message.answer("🤔 Ovozdan anime nomini aniqlay olmadim.")
        return
    except AIServiceError as exc:
        logger.error("AI audio xatosi: %s", exc, exc_info=True)
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Ovozni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
        return

    await _delete_thinking(thinking_msg)
    await message.answer(f"🎬 Siz shu haqda so'ragandirsiz: <b>{anime_name}</b>")
    await container.analytics_service.log_event("ai_voice_request", user_id=db_user.user_id)


# --------------------------------------------------------------------------
# Audio fayl (voice emas, musiqa/fayl sifatida yuborilgan)
# --------------------------------------------------------------------------
@router.message(AIChatStates.chatting, F.audio)
async def ai_chat_audio_file(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    if not await require_vip_for_ai(message, container, db_user):
        await state.clear()
        return

    if message.audio.file_size and message.audio.file_size > _MAX_MEDIA_BYTES:
        await message.answer("⚠️ Audio hajmi juda katta.")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await _send_thinking(message)

    try:
        audio_bytes = await _download_file_bytes(message, message.audio.file_id)
        anime_name = await container.gemini_client.transcribe_audio(
            audio_bytes=audio_bytes,
            mime_type=message.audio.mime_type or "audio/mpeg",
        )
    except RateLimitExceededError:
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
        return
    except AIResponseEmptyError:
        await _delete_thinking(thinking_msg)
        await message.answer("🤔 Audio'dan anime nomini aniqlay olmadim.")
        return
    except AIServiceError as exc:
        logger.error("AI audio-fayl xatosi: %s", exc, exc_info=True)
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Audio-ni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
        return

    await _delete_thinking(thinking_msg)
    await message.answer(f"🎬 Siz shu haqda so'ragandirsiz: <b>{anime_name}</b>")
    await container.analytics_service.log_event("ai_audio_request", user_id=db_user.user_id)


# --------------------------------------------------------------------------
# Video orqali anime qidirish
# --------------------------------------------------------------------------
@router.message(AIChatStates.chatting, F.video)
async def ai_chat_video(
    message: Message, state: FSMContext, container: Container, db_user: User
) -> None:
    if not await require_vip_for_ai(message, container, db_user):
        await state.clear()
        return

    if message.video.file_size and message.video.file_size > _MAX_MEDIA_BYTES:
        await message.answer("⚠️ Video hajmi juda katta.")
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await _send_thinking(message)

    try:
        video_bytes = await _download_file_bytes(message, message.video.file_id)
        anime_name = await container.gemini_client.identify_anime_from_video(
            video_bytes=video_bytes,
            mime_type=message.video.mime_type or "video/mp4",
        )
    except RateLimitExceededError:
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Kunlik AI so'rovlar limitiga yetdingiz. Ertaga qayta urinib ko'ring.")
        return
    except AIResponseEmptyError:
        await _delete_thinking(thinking_msg)
        await message.answer("🤔 Videodan anime nomini aniqlay olmadim.")
        return
    except AIServiceError as exc:
        logger.error("AI video xatosi: %s", exc, exc_info=True)
        await _delete_thinking(thinking_msg)
        await message.answer("⚠️ Videoni tanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.")
        return

    await _delete_thinking(thinking_msg)
    await message.answer(f"🎬 Bu anime shunga o'xshaydi: <b>{anime_name}</b>")
    await container.analytics_service.log_event("ai_video_request", user_id=db_user.user_id)