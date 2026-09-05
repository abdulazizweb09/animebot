# Anime Telegram Bot

To'liq funksional anime Telegram bot: qidiruv, kategoriyalar, sevimlilar,
ko'rish tarixi, VIP obuna tizimi, AI yordamchi (Gemini), va to'liq admin
panel (anime/video boshqaruvi, broadcast, statistika, backup, granular
ruxsatlar).

Ma'lumotlar bazasi sifatida **JSON fayllar** ishlatiladi (`json/` papkasi),
lekin ular hech qachon to'g'ridan-to'g'ri o'qilmaydi/yozilmaydi — faqat
`database/json_manager.py` dagi `JsonManager` orqali (atomic write, lock,
cache bilan). Arxitektura tafsilotlari uchun `ARCHITECTURE.md` ga qarang.

## O'rnatish

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Sozlash

1. `.env.example` faylini `.env` deb nusxalang:
   ```bash
   cp .env.example .env
   ```
2. `.env` faylini to'ldiring:
   - `BOT_TOKEN` — @BotFather dan olingan token
   - `MAIN_ADMIN_IDS` — sizning Telegram ID'ingiz (vergul bilan bir nechta
     bo'lishi mumkin). O'z ID'ingizni bilish uchun @userinfobot ga yozing.
   - `GEMINI_API_KEY` — https://aistudio.google.com/apikey dan olingan kalit
   - Qolgan qiymatlar ixtiyoriy, standart qiymatlar bilan ishlayveradi.

## Ishga tushirish

```bash
python main.py
```

Bot birinchi marta ishga tushganda `json/` papkasidagi barcha kerakli
fayllar (`users.json`, `anime.json`, ...) avtomatik yaratiladi.

## Admin panel

Botga `MAIN_ADMIN_IDS` da ko'rsatilgan ID bilan `/admin` buyrug'ini yuboring.

Asosiy admin (`MAIN_ADMIN_IDS`) barcha huquqlarga ega va qo'shimcha
adminlarni ("👮 Adminlar" bo'limi orqali) qo'sha oladi. Har bir qo'shimcha
adminga alohida-alohida ruxsatlar berish mumkin ("🔑 Ruxsatlar" bo'limi):

- `anime_add`, `anime_edit`, `anime_delete`
- `video_add`, `video_delete`
- `broadcast_send`
- `vip_approve`
- `subscription_manage`
- `backup_create`
- `logs_view`

## Majburiy obuna kanali sozlash

Bot kanalga **admin** sifatida qo'shilgan bo'lishi kerak (a'zolikni
tekshirish uchun). Keyin admin panelda "🔗 Majburiy obuna" bo'limidan kanal
ID/username/link kiritiladi.

## Papka tuzilishi

To'liq tavsif uchun `ARCHITECTURE.md` ga qarang. Qisqacha:

```
config/         — .env, enum, konstantalar
database/       — JsonManager, modellar, repositorylar
services/       — biznes-mantiq
handlers/user/  — foydalanuvchi handlerlari
handlers/admin/ — admin panel handlerlari
keyboards/      — inline/reply klaviaturalar
middlewares/    — container, user, throttling, flood-protection
filters/        — admin filterlari
states/         — FSM state guruhlari
ai/             — Gemini client va promptlar
locales/        — uz/ru/en tarjimalar
json/           — runtime ma'lumotlar (git-ignore qilingan)
backup/         — avtomatik va qo'lda yaratilgan backup ZIP fayllar
logs/           — runtime loglar
```

## Backup / Restore

- Admin panelda "💾 Backup" tugmasi — barcha JSON fayllarni ZIP qilib
  yuboradi.
- Bot avtomatik ravishda har `BACKUP_AUTO_INTERVAL_HOURS` soatda (standart:
  6 soat) backup yaratadi (`backup/` papkasida, oxirgi 10 tasi saqlanadi).
- Tiklash uchun: ZIP faylni botga **caption qilib aynan `/restore_backup`
  yozib** yuboring (faqat asosiy admin). ⚠️ Bu amal joriy barcha
  ma'lumotlarni backup'dagi bilan almashtiradi — ehtiyot bo'ling.

## Xavfsizlik

- **Rate limiting** — har bir foydalanuvchi uchun so'rovlar orasidagi
  minimal interval (`ThrottlingMiddleware`); VIP foydalanuvchilar tezroq.
- **Flood protection** — belgilangan oynada juda ko'p xabar yuborgan
  foydalanuvchi vaqtincha bloklanadi (`FloodMiddleware`).
- **Ban tizimi** — admin istalgan foydalanuvchini bloklashi mumkin, bloklangan
  foydalanuvchi botdan foydalana olmaydi.

## Kengaytirish

Yangi funksiya qo'shish bo'yicha qo'llanma `ARCHITECTURE.md` faylining
"Kengaytirilishi" bo'limida keltirilgan.
# animebot
