"""Barcha admin handlerlarini bitta routerga yig'adi."""

from aiogram import Router

from handlers.admin.admin_management import router as admin_management_router
from handlers.admin.anime_admin import router as anime_admin_router
from handlers.admin.backup_admin import backup_restore_router, router as backup_router
from handlers.admin.ban import router as ban_router
from handlers.admin.broadcast import router as broadcast_router
from handlers.admin.collection_admin import router as collection_router
from handlers.admin.content_admin import router as content_router
from handlers.admin.episode_admin import router as episode_router
from handlers.admin.episode_extra_admin import router as episode_extra_router
from handlers.admin.hidden_admin import router as hidden_router
from handlers.admin.logs_admin import router as logs_router
from handlers.admin.panel import router as panel_router
from handlers.admin.poll_admin import router as poll_admin_router
from handlers.admin.promo_admin import router as promo_router
from handlers.admin.request_admin import router as request_router
from handlers.admin.schedule_admin import router as schedule_router
from handlers.admin.stats import router as stats_router
from handlers.admin.subscription_admin import router as subscription_router
from handlers.admin.user_lookup_admin import router as user_lookup_router
from handlers.admin.vip_admin import router as vip_admin_router

admin_router = Router(name="admin")
for r in (
    panel_router,
    anime_admin_router,
    episode_router,
    episode_extra_router,
    hidden_router,
    collection_router,
    content_router,
    poll_admin_router,
    promo_router,
    request_router,
    user_lookup_router,
    schedule_router,
    vip_admin_router,
    broadcast_router,
    stats_router,
    logs_router,
    subscription_router,
    ban_router,
    backup_router,
    backup_restore_router,
    admin_management_router,
):
    admin_router.include_router(r)

__all__ = ["admin_router"]
