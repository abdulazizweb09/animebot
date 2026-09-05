# Anime Telegram Bot — Arxitektura

## Umumiy g'oya

Bot **Clean Architecture** asosida, aiogram 3.x da yoziladi. Ma'lumotlar bazasi
o'rniga **JSON fayllar** ishlatiladi, lekin ular hech qachon to'g'ridan-to'g'ri
o'qilmaydi/yozilmaydi — faqat `JsonManager` orqali, atomic write + file lock +
in-memory cache bilan.

## Qatlamlar (Layers)

```
Telegram Update
      │
      ▼
Middlewares (throttling, i18n, user injection, logging)
      │
      ▼
Filters (admin filter, vip filter, state filter)
      │
      ▼
Handlers (faqat: inputni qabul qilish → Service chaqirish → javob yuborish)
      │
      ▼
Services (biznes-mantiq: UserService, AnimeService, VipService, AIService ...)
      │
      ▼
Repositories (database/repositories/*) — Service bilan JSON o'rtasidagi qatlam,
      faqat repository JsonManager bilan gaplashadi
      │
      ▼
JsonManager (database/json_manager.py) — yagona joy, JSON fayllar bilan
      xavfsiz ishlaydigan qator
      │
      ▼
json/*.json — fayllar
```

**Qoida:** Handler hech qachon to'g'ridan-to'g'ri JSON o'qimaydi/yozmaydi.
Handler faqat Service chaqiradi. Service faqat Repository chaqiradi.
Repository faqat JsonManager chaqiradi.

## Papkalar vazifasi

| Papka | Vazifa |
|---|---|
| `config/` | .env dan sozlamalarni o'qish, konstantalar, enum'lar |
| `database/` | JsonManager + repositories (har bir JSON fayl uchun repository) |
| `database/models/` | dataclass modellar (User, Anime, Episode, Vip, ...) |
| `services/` | Biznes-mantiq (user, anime, vip, ai, search, backup, broadcast ...) |
| `handlers/user/` | Oddiy foydalanuvchi handlerlari |
| `handlers/admin/` | Admin panel handlerlari |
| `middlewares/` | Throttling, i18n, DB-injection, logging, error-catch |
| `filters/` | IsAdmin, IsMainAdmin, IsVip, HasPermission, StateFilter |
| `states/` | FSM state guruhlari (aiogram StatesGroup) |
| `keyboards/user/` | Foydalanuvchi uchun inline/reply klaviaturalar |
| `keyboards/admin/` | Admin uchun inline/reply klaviaturalar |
| `ai/` | Gemini client, promptlar, conversation-history menejeri |
| `utils/` | Umumiy yordamchi funksiyalar (fuzzy search, validators, formatters) |
| `backup/` | Backup/restore logikasi, ZIP yaratish |
| `logs/` | Runtime log fayllari (bot yozadi, git-ignore qilinadi) |
| `assets/` | Statik fayllar (masalan, default rasm) |
| `json/` | Barcha ma'lumotlar shu yerda saqlanadi |

## Ishga tushirish oqimi

1. `main.py` — `.env` yuklaydi → `config` obyektini quradi
2. `JsonManager` barcha kerakli JSON fayllarni tekshiradi, yo'q bo'lsa yaratadi
   (`auto_create`)
3. Dispatcher yaratiladi, barcha middleware/filter/router ro'yxatdan o'tkaziladi
4. Polling boshlanadi

## Kengaytirilishi

Yangi funksiya (masalan, "Manga") qo'shish uchun:
1. `database/models/manga.py` — model
2. `database/repositories/manga_repository.py` — repository
3. `services/manga_service.py` — biznes-mantiq
4. `handlers/user/manga.py` — handlerlar
5. `keyboards/user/manga.py` — klaviaturalar
6. `json/manga.json` — avtomatik yaratiladi

Mavjud qatlamlarga tegmasdan, faqat yangi fayllar qo'shish orqali kengaytiriladi
(Open/Closed Principle).
