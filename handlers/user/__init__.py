"""Foydalanuvchi handlerlarini bitta routerga yig'adi.

MUHIM: hub routerlar (search_hub, profile_hub, guide) ro'yxatning
BOSHIDA turishi kerak — chunki ular yangi soddalashtirilgan asosiy
menyu tugmalariga (F.text.in_(all_variants("btn_..."))) javob beradi,
va aiogram bir update uchun faqat birinchi mos keluvchi handlerni
ishga tushiradi.
"""

from aiogram import Router

from handlers.user.advanced import router as advanced_router
from handlers.user.ai_assistant import router as ai_router
from handlers.user.anime_detail import router as anime_detail_router
from handlers.user.calendar import router as calendar_router
from handlers.user.categories import router as categories_router
from handlers.user.character_search import router as character_search_router
from handlers.user.collections import router as collections_router
from handlers.user.discover import router as discover_router
from handlers.user.economy import router as economy_router
from handlers.user.extra_info import router as extra_info_router
from handlers.user.favorites import router as favorites_router
from handlers.user.guide import router as guide_router
from handlers.user.history import router as history_router
from handlers.user.misc import router as misc_router
from handlers.user.news import router as news_router
from handlers.user.notifications import router as notifications_router
from handlers.user.poll import router as poll_router
from handlers.user.profile import router as profile_router
from handlers.user.profile_hub import router as profile_hub_router
from handlers.user.promo import router as promo_router
from handlers.user.random_anime import router as random_router
from handlers.user.rating import router as rating_router
from handlers.user.recommendation import router as recommendation_router
from handlers.user.referral import router as referral_router
from handlers.user.search import router as search_router
from handlers.user.search_hub import router as search_hub_router
from handlers.user.settings import router as settings_router
from handlers.user.shop import router as shop_router
from handlers.user.start import router as start_router
from handlers.user.studio_search import router as studio_router
from handlers.user.vip import router as vip_router
from handlers.user.watchlist import router as watchlist_router

user_router = Router(name="user")
for r in (
    start_router,
    # --- Yangi soddalashtirilgan asosiy menyu hub'lari (birinchi bo'lib
    # tekshiriladi, chunki ular asosiy reply-tugmalarga javob beradi) ---
    search_hub_router,
    profile_hub_router,
    guide_router,
    # --- Ichki (hub orqali chaqiriladigan) funksional routerlar ---
    search_router,
    categories_router,
    discover_router,
    recommendation_router,
    random_router,
    collections_router,
    studio_router,
    advanced_router,
    economy_router,
    shop_router,
    calendar_router,
    character_search_router,
    news_router,
    poll_router,
    rating_router,
    notifications_router,
    favorites_router,
    history_router,
    watchlist_router,
    anime_detail_router,
    extra_info_router,
    profile_router,
    settings_router,
    referral_router,
    promo_router,
    vip_router,
    ai_router,
    misc_router,
):
    user_router.include_router(r)

__all__ = ["user_router"]
