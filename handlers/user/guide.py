"""📖 Qo'llanma — botdan to'liq foydalanish bo'yicha yo'riqnoma.

Yangi (soddalashtirilgan, 5 tugmali) menyu tuzilishiga mos ravishda,
foydalanuvchiga har bir bo'lim nima qilishini tushuntiradi.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from database.models.user import User
from utils.i18n import all_variants

router = Router(name="user_guide")


_GUIDE_TEXT_UZ = """📖 <b>Botdan qanday foydalanish mumkin — to'liq qo'llanma</b>

Bot 5 ta asosiy bo'limdan iborat:

🔍 <b>Anime izlash</b>
Bu yerdan siz:
  • 🔎 Nom bo'yicha qidirishingiz (matn, 🎙 ovozli xabar yoki 🖼 poster rasmi orqali — VIP kerak)
  • 🗂 Janr (kategoriya) bo'yicha ko'rishingiz
  • 🔥 Trend/Top/Yangi qo'shilgan animelarni ko'rishingiz
  • 🎯 Sizga moslashtirilgan tavsiyalarni olishingiz
  • 🎲 Tasodifiy anime tanlashingiz
  • 🎞 Kolleksiyalar (franchise)ni ko'rishingiz
  • 🎬 Studiya bo'yicha qidirishingiz
  • 🧰 Kengaytirilgan filter (janr+yil+studiya+reyting)dan foydalanishingiz
  • 📅 Chiqish kalendarini ko'rishingiz
  • 🧑‍🎤 Personaj/ovoz beruvchi aktyor bo'yicha qidirishingiz mumkin.

Anime kartochkasida: epizodlarni ko'rish, sevimlilarga qo'shish,
baholash, izoh qoldirish, do'stlarga ulashish va "o'xshash animelar"ni
ko'rish imkoniyatlari bor.

💎 <b>VIP</b>
VIP reja sotib olib, quyidagi imtiyozlarga ega bo'lasiz:
  • 🤖 AI Yordamchi (chat, ovozli/rasm orqali qidiruv)
  • 🔓 Majburiy obunadan ozodlik
  • ⚡️ Tezroq javob (throttling yo'q)
  • 🌟 Loyallik darajasi (Bronze/Silver/Gold) — VIP kunlari yig'ilib boradi
    va kunlik bonusga qo'shimcha foiz beradi
  • 💎 VIP-only animelarga kirish

🤖 <b>AI Yordamchi</b> (faqat VIP)
Anime haqida savol bering, tavsiya so'rang — sun'iy intellekt yordam beradi.

👤 <b>Profil</b>
Shaxsiy bo'lim — bu yerda:
  • 👤 Profil ma'lumotlari (XP, daraja, tanga, VIP holati)
  • ❤️ Sevimlilar
  • 📌 Ro'yxatlarim (Watching/Completed/Dropped/Plan to Watch)
  • 🏅 Reyting (TOP foydalanuvchilar)
  • 🛍 Tanga do'koni (tangalarni sarflash)
  • 🏆 Yutuqlarim (badge'lar)
  • ▶️ Davom etish (oxirgi ko'rilgan animelar)
  • ⚙️ Sozlamalar (til, bildirishnoma, ma'lumot eksporti va h.k.)
  • 🎟 Promo-kodlar
  • 👥 Do'st taklif qilish (referral)
  • ➕ Boshqa: Tarix, Bildirishnomalar, Yangiliklar, Viktorina, So'rovlar

💰 <b>Tanga va XP qanday to'planadi?</b>
  • Har bir ko'rilgan epizod uchun XP + tanga
  • Kunlik bonus (ketma-ket kunlar uchun ortib boradi)
  • Do'st taklif qilish
  • Viktorinada to'g'ri javob berish
  • Promo-kod orqali

Savolingiz bo'lsa, ⚙️ Sozlamalar → 🐛 Muammo haqida xabar berish orqali
bizga yozing!"""


@router.message(F.text.in_(all_variants("btn_guide")))
async def show_guide(message: Message, db_user: User) -> None:
    # Hozircha faqat uz tilida to'liq qo'llanma — boshqa tillar uchun ham
    # bir xil matn ko'rsatiladi (tarjima keyinroq to'ldirilishi mumkin).
    await message.answer(_GUIDE_TEXT_UZ)
