# """Gemini API bilan ishlaydigan yupqa (thin) client wrapper."""

# from __future__ import annotations

# from google import genai
# from google.genai import types

# from config.constants import CONSTANTS
# from utils.exceptions import AIResponseEmptyError, AIServiceError
# from utils.logger import get_logger

# logger = get_logger(__name__)


# class GeminiClient:
#     def __init__(self, api_key: str, model_name: str) -> None:
#         self._client = genai.Client(api_key=api_key)
#         self._model_name = model_name

#     def _config(self, system_prompt: str) -> types.GenerateContentConfig:
#         return types.GenerateContentConfig(
#             system_instruction=system_prompt,
#             max_output_tokens=CONSTANTS.AI_MAX_OUTPUT_TOKENS,
#             temperature=CONSTANTS.AI_TEMPERATURE,
#             automatic_function_calling=types.AutomaticFunctionCallingConfig(
#             # maximum_remote_calls=20,
#             disable=True
#         ),
#         )

#     async def generate_reply(
#         self,
#         system_prompt: str,
#         history: list[dict[str, str]],
#         user_message: str,
#     ) -> str:
#         """history — [{"role": "user"|"model", "text": "..."}] formatida."""

#         try:
#             contents = [
#                 types.Content(
#                     role=h["role"],
#                     parts=[types.Part.from_text(text=h["text"])],
#                 )
#                 for h in history
#             ]

#             contents.append(
#                 types.Content(
#                     role="user",
#                     parts=[types.Part.from_text(text=user_message)],
#                 )
#             )

#             response = await self._client.aio.models.generate_content(
#                 model=self._model_name,
#                 contents=contents,
#                 config=self._config(system_prompt),
#             )

#             text = (response.text or "").strip()

#         except Exception as exc:  # noqa: BLE001
#             logger.error("Gemini API xatosi: %s", exc)
#             raise AIServiceError(
#                 f"AI javob berolmadi: {exc}"
#             ) from exc

#         if not text:
#             raise AIResponseEmptyError("AI bo'sh javob qaytardi.")

#         return text

#     async def transcribe_audio(
#         self,
#         audio_bytes: bytes,
#         mime_type: str,
#     ) -> str:
#         """Audio xabardan anime nomini aniqlaydi."""

#         prompt = (
#             "Ushbu audio xabarda foydalanuvchi qanday anime nomini "
#             "qidirayotganini ayt. FAQAT anime nomini (yoki eng yaqin "
#             "taxminni) qaytar, boshqa hech qanday izoh yozma."
#         )

#         try:
#             response = await self._client.aio.models.generate_content(
#                 model=self._model_name,
#                 contents=[
#                     types.Part.from_text(text=prompt),
#                     types.Part.from_bytes(
#                         data=audio_bytes,
#                         mime_type=mime_type,
#                     ),
#                 ],
#             )

#             text = (response.text or "").strip()

#         except Exception as exc:  # noqa: BLE001
#             logger.error("Gemini audio transkripsiya xatosi: %s", exc)
#             raise AIServiceError(
#                 f"Audio tanib bo'lmadi: {exc}"
#             ) from exc

#         if not text:
#             raise AIResponseEmptyError("Audio'dan matn olinmadi.")

#         return text

#     async def identify_anime_from_image(
#         self,
#         image_bytes: bytes,
#         mime_type: str,
#     ) -> str:
#         """Poster/skrinshotdan anime nomini aniqlaydi."""

#         prompt = (
#             "Bu rasmda qaysi anime tasvirlangan? FAQAT anime nomini "
#             "(ingliz yoki original nomi bilan) qaytar, boshqa hech qanday "
#             "izoh yozma. Agar aniq bilmasang, eng yaqin taxminingni yoz."
#         )

#         try:
#             response = await self._client.aio.models.generate_content(
#                 model=self._model_name,
#                 contents=[
#                     types.Part.from_text(text=prompt),
#                     types.Part.from_bytes(
#                         data=image_bytes,
#                         mime_type=mime_type,
#                     ),
#                 ],
#             )

#             text = (response.text or "").strip()

#         except Exception as exc:  # noqa: BLE001
#             logger.error("Gemini rasm tanish xatosi: %s", exc)
#             raise AIServiceError(
#                 f"Rasmni tanib bo'lmadi: {exc}"
#             ) from exc

#         if not text:
#             raise AIResponseEmptyError(
#                 "Rasmdan anime nomi aniqlanmadi."
#             )

#         return text


"""Gemini API bilan ishlaydigan yupqa (thin) client wrapper."""

from __future__ import annotations

from google import genai
from google.genai import types

from config.constants import CONSTANTS
from utils.exceptions import AIResponseEmptyError, AIServiceError
from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def _config(
        self,
        system_prompt: str | None = None,
    ) -> types.GenerateContentConfig:
        """Har bir so'rov uchun umumiy config.

        system_prompt berilmasa ham (masalan rasm/audio tanish uchun),
        max_output_tokens va temperature har doim qo'llanadi — shu
        ikkitasi bo'lmagani uchun avval javoblar kesilib/bo'sh qaytardi.
        """

        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=CONSTANTS.AI_MAX_OUTPUT_TOKENS,
            temperature=CONSTANTS.AI_TEMPERATURE,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                # maximum_remote_calls=20,
                disable=True
            ),
        )

    async def generate_reply(
        self,
        system_prompt: str,
        history: list[dict[str, str]],
        user_message: str,
    ) -> str:
        """history — [{"role": "user"|"model", "text": "..."}] formatida."""

        try:
            contents = [
                types.Content(
                    role=h["role"],
                    parts=[types.Part.from_text(text=h["text"])],
                )
                for h in history
            ]

            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )

            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=self._config(system_prompt),
            )

            text = (response.text or "").strip()

        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini API xatosi: %s", exc, exc_info=True)
            raise AIServiceError(
                f"AI javob berolmadi: {exc}"
            ) from exc

        if not text:
            raise AIResponseEmptyError("AI bo'sh javob qaytardi.")

        return text

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str,
    ) -> str:
        """Audio xabardan anime nomini aniqlaydi."""

        system_prompt = (
            "Sen anime nomlarini audio orqali aniqlovchi yordamchisan. "
            "Foydalanuvchi audio xabarda qanday anime haqida gapirayotganini "
            "aniqla."
        )

        prompt = (
            "Ushbu audio xabarda foydalanuvchi qanday anime nomini "
            "qidirayotganini ayt. FAQAT anime nomini (yoki eng yaqin "
            "taxminni) qaytar, boshqa hech qanday izoh yozma."
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type,
                    ),
                ],
                config=self._config(system_prompt),
            )

            text = (response.text or "").strip()

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Gemini audio transkripsiya xatosi: %s", exc, exc_info=True
            )
            raise AIServiceError(
                f"Audio tanib bo'lmadi: {exc}"
            ) from exc

        if not text:
            raise AIResponseEmptyError("Audio'dan matn olinmadi.")

        return text

    async def identify_anime_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        """Poster/skrinshotdan anime nomini aniqlaydi."""

        system_prompt = (
            "Sen anime nomlarini rasm (poster/skrinshot) orqali "
            "aniqlovchi yordamchisan."
        )

        prompt = (
            "Bu rasmda qaysi anime tasvirlangan? FAQAT anime nomini "
            "(ingliz yoki original nomi bilan) qaytar, boshqa hech qanday "
            "izoh yozma. Agar aniq bilmasang, eng yaqin taxminingni yoz."
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                ],
                config=self._config(system_prompt),
            )

            text = (response.text or "").strip()

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Gemini rasm tanish xatosi: %s", exc, exc_info=True
            )
            raise AIServiceError(
                f"Rasmni tanib bo'lmadi: {exc}"
            ) from exc

        if not text:
            raise AIResponseEmptyError(
                "Rasmdan anime nomi aniqlanmadi."
            )

        return text

    async def identify_anime_from_video(
        self,
        video_bytes: bytes,
        mime_type: str,
    ) -> str:
        """Video/skrinshot-videodan anime nomini aniqlaydi.

        Eslatma: bu metod avval umuman mavjud emas edi, shuning uchun
        video yuborilganda handler tarafida AttributeError chiqishi
        kerak edi. Agar handleringiz boshqa metod nomini chaqirayotgan
        bo'lsa, o'sha joyda ushbu nomga moslashtiring:
        `identify_anime_from_video`.
        """

        system_prompt = (
            "Sen anime nomlarini video parchasi orqali aniqlovchi "
            "yordamchisan."
        )

        prompt = (
            "Bu videoda qaysi anime tasvirlangan? FAQAT anime nomini "
            "(ingliz yoki original nomi bilan) qaytar, boshqa hech qanday "
            "izoh yozma. Agar aniq bilmasang, eng yaqin taxminingni yoz."
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(
                        data=video_bytes,
                        mime_type=mime_type,
                    ),
                ],
                config=self._config(system_prompt),
            )

            text = (response.text or "").strip()

        except Exception as exc:  
            logger.error(
                "Gemini video tanish xatosi: %s", exc, exc_info=True
            )
            raise AIServiceError(
                f"Videoni tanib bo'lmadi: {exc}"
            ) from exc

        if not text:
            raise AIResponseEmptyError(
                "Videodan anime nomi aniqlanmadi."
            )

        return text