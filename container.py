# """Oddiy dependency-injection konteyner.

# aiogram middleware orqali ``data["container"]`` sifatida handlerlarga
# uzatiladi. Barcha repository va servicelar shu yerda bitta joyda "wire"
# qilinadi — handlerlar hech qachon ``JsonManager``ni to'g'ridan-to'g'ri
# ko'rmaydi.
# """

# from __future__ import annotations

# from dataclasses import dataclass
# from functools import lru_cache

# from ai.gemini_client import GeminiClient
# from config.constants import CONSTANTS
# from config.settings import Settings, get_settings
# from database.json_manager import JsonManager
# from database.repositories import (
#     AnimeRepository,
#     EpisodeRepository,
#     UserRepository,
#     VideoRepository,
#     VipRepository,
# )
# from database.repositories.admin_repository import AdminRepository
# from database.repositories.achievement_repository import AchievementRepository
# from database.repositories.collection_repository import CollectionRepository
# from database.repositories.economy_repository import EconomyRepository
# from database.repositories.interaction_repository import (
#     FavoriteRepository,
#     HistoryRepository,
#     WatchlistRepository,
# )
# from database.repositories.promo_repository import PromoRepository
# from database.repositories.referral_repository import ReferralRepository
# from database.repositories.schedule_repository import ScheduleRepository
# from database.repositories.character_repository import CharacterRepository
# from database.repositories.media_gallery_repository import MediaGalleryRepository
# from database.repositories.news_repository import NewsRepository
# from database.repositories.poll_repository import PollRepository, QuizRepository
# from database.repositories.alias_repository import AliasRepository
# from database.repositories.rating_repository import (
#     CommentRepository,
#     NotificationRepository,
#     RatingRepository,
# )
# from database.repositories.search_history_repository import SearchHistoryRepository
# from database.repositories.request_repository import AnimeRequestRepository, BugReportRepository
# from services.personal_stats_service import PersonalStatsService
# from services.request_service import AnimeRequestService, BugReportService
# from services.achievement_service import AchievementService
# from services.admin_service import AdminService
# from services.ai_service import AIService
# from services.analytics_service import AnalyticsService
# from services.anime_service import AnimeService
# from services.audit_log_service import AuditLogService
# from services.backup_service import BackupService
# from services.audience_service import AudienceService
# from services.broadcast_service import BroadcastService
# from services.character_service import CharacterService
# from services.collection_service import CollectionService
# from services.economy_service import EconomyService
# from services.favorite_service import FavoriteService
# from services.health_service import HealthService
# from services.history_service import HistoryService
# from services.list_cache_service import ListCacheService
# from services.maintenance_service import MaintenanceService
# from services.news_service import NewsService
# from services.notification_service import NotificationService
# from services.permission_service import PermissionService
# from services.poll_service import PollService, QuizService
# from services.promo_service import PromoService
# from services.rating_service import CommentService, RatingService
# from services.recommendation_service import RecommendationService
# from services.referral_service import ReferralService
# from services.schedule_service import ScheduleService
# from services.search_service import SearchService
# from services.stats_service import StatsService
# from services.subscription_service import SubscriptionService
# from services.user_service import UserService
# from services.vip_service import VipService
# from services.watchlist_service import WatchlistService


# @dataclass
# class Container:
#     settings: Settings
#     manager: JsonManager

#     users: UserRepository
#     animes: AnimeRepository
#     episodes: EpisodeRepository
#     videos: VideoRepository
#     vips: VipRepository
#     favorites: FavoriteRepository
#     history: HistoryRepository
#     watchlist: WatchlistRepository
#     admins: AdminRepository
#     collections: CollectionRepository
#     achievements: AchievementRepository
#     economy: EconomyRepository
#     promos: PromoRepository
#     referrals: ReferralRepository
#     schedule: ScheduleRepository
#     characters: CharacterRepository
#     media_gallery: MediaGalleryRepository
#     news: NewsRepository
#     polls: PollRepository
#     quizzes: QuizRepository
#     ratings: RatingRepository
#     comments: CommentRepository
#     notifications: NotificationRepository
#     aliases: AliasRepository
#     search_history: SearchHistoryRepository
#     anime_requests: AnimeRequestRepository
#     bug_reports: BugReportRepository

#     user_service: UserService
#     subscription_service: SubscriptionService
#     anime_service: AnimeService
#     search_service: SearchService
#     favorite_service: FavoriteService
#     history_service: HistoryService
#     list_cache: ListCacheService
#     vip_service: VipService
#     permission_service: PermissionService
#     audit_service: AuditLogService
#     admin_service: AdminService
#     broadcast_service: BroadcastService
#     audience_service: AudienceService
#     stats_service: StatsService
#     backup_service: BackupService
#     ai_service: AIService
#     analytics_service: AnalyticsService
#     collection_service: CollectionService
#     watchlist_service: WatchlistService
#     achievement_service: AchievementService
#     economy_service: EconomyService
#     promo_service: PromoService
#     referral_service: ReferralService
#     recommendation_service: RecommendationService
#     schedule_service: ScheduleService
#     character_service: CharacterService
#     news_service: NewsService
#     poll_service: PollService
#     quiz_service: QuizService
#     rating_service: RatingService
#     comment_service: CommentService
#     notification_service: NotificationService
#     maintenance_service: MaintenanceService
#     anime_request_service: AnimeRequestService
#     bug_report_service: BugReportService
#     health_service: HealthService | None = None
#     personal_stats_service: PersonalStatsService | None = None


# @lru_cache(maxsize=1)
# def get_container() -> Container:
#     settings = get_settings()
#     manager = JsonManager(
#         base_dir=settings.json_dir,
#         backup_dir=settings.backup_path,
#         cache_ttl_seconds=300,
#         cache_max_entries=512,
#     )

#     users = UserRepository(manager)
#     animes = AnimeRepository(manager)
#     episodes = EpisodeRepository(manager)
#     videos = VideoRepository(manager)
#     vips = VipRepository(manager)
#     favorites = FavoriteRepository(manager)
#     history = HistoryRepository(manager)
#     watchlist = WatchlistRepository(manager)
#     admins = AdminRepository(manager)
#     collections = CollectionRepository(manager)
#     achievements = AchievementRepository(manager)
#     economy = EconomyRepository(manager)
#     promos = PromoRepository(manager)
#     referrals = ReferralRepository(manager)
#     schedule = ScheduleRepository(manager)
#     characters = CharacterRepository(manager)
#     media_gallery = MediaGalleryRepository(manager)
#     news = NewsRepository(manager)
#     polls = PollRepository(manager)
#     quizzes = QuizRepository(manager)
#     ratings = RatingRepository(manager)
#     comments = CommentRepository(manager)
#     notifications = NotificationRepository(manager)
#     aliases = AliasRepository(manager)
#     search_history = SearchHistoryRepository(manager)
#     anime_requests = AnimeRequestRepository(manager)
#     bug_reports = BugReportRepository(manager)

#     permission_service = PermissionService(manager, settings)
#     audit_service = AuditLogService(manager)
#     analytics_service = AnalyticsService(manager)
#     vip_service = VipService(vips, settings)

#     container_instance = Container(
#         settings=settings,
#         manager=manager,
#         users=users,
#         animes=animes,
#         episodes=episodes,
#         videos=videos,
#         vips=vips,
#         favorites=favorites,
#         history=history,
#         watchlist=watchlist,
#         admins=admins,
#         collections=collections,
#         achievements=achievements,
#         economy=economy,
#         promos=promos,
#         referrals=referrals,
#         schedule=schedule,
#         characters=characters,
#         media_gallery=media_gallery,
#         news=news,
#         polls=polls,
#         quizzes=quizzes,
#         ratings=ratings,
#         comments=comments,
#         notifications=notifications,
#         aliases=aliases,
#         search_history=search_history,
#         anime_requests=anime_requests,
#         bug_reports=bug_reports,
#         user_service=UserService(users, settings),
#         subscription_service=SubscriptionService(manager),
#         anime_service=AnimeService(animes, episodes, videos, analytics_service),
#         search_service=SearchService(animes, aliases, search_history),
#         favorite_service=FavoriteService(favorites),
#         history_service=HistoryService(history),
#         list_cache=ListCacheService(),
#         vip_service=vip_service,
#         permission_service=permission_service,
#         audit_service=audit_service,
#         admin_service=AdminService(admins, users, permission_service, audit_service, manager),
#         broadcast_service=BroadcastService(manager, users),
#         audience_service=AudienceService(users, vips, favorites, animes),
#         stats_service=StatsService(users, animes, vips),
#         backup_service=BackupService(manager, settings.json_dir, settings.backup_path),
#         ai_service=AIService(
#             manager,
#             GeminiClient(settings.gemini_api_key, settings.gemini_model),
#             animes,
#             users,
#             daily_limit=CONSTANTS.AI_DAILY_LIMIT,
#         ),
#         analytics_service=analytics_service,
#         collection_service=CollectionService(collections, animes),
#         watchlist_service=WatchlistService(watchlist, animes, episodes),
#         achievement_service=AchievementService(achievements),
#         economy_service=EconomyService(economy, vip_service),
#         promo_service=PromoService(promos, vips, economy),
#         referral_service=ReferralService(referrals, economy, users),
#         recommendation_service=RecommendationService(animes, favorites, history),
#         schedule_service=ScheduleService(schedule, animes),
#         character_service=CharacterService(characters, media_gallery),
#         news_service=NewsService(news),
#         poll_service=PollService(polls),
#         quiz_service=QuizService(quizzes, economy),
#         rating_service=RatingService(ratings, animes),
#         comment_service=CommentService(comments),
#         notification_service=NotificationService(notifications, users),
#         maintenance_service=MaintenanceService(manager),
#         anime_request_service=AnimeRequestService(anime_requests),
#         bug_report_service=BugReportService(bug_reports),
#     )
#     container_instance.health_service = HealthService(container_instance)
#     container_instance.personal_stats_service = PersonalStatsService(container_instance)
#     return container_instance


"""Oddiy dependency-injection konteyner.

aiogram middleware orqali ``data["container"]`` sifatida handlerlarga
uzatiladi. Barcha repository va servicelar shu yerda bitta joyda "wire"
qilinadi — handlerlar hech qachon ``JsonManager``ni to'g'ridan-to'g'ri
ko'rmaydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ai.gemini_client import GeminiClient
from config.constants import CONSTANTS
from config.settings import Settings, get_settings
from database.json_manager import JsonManager
from database.repositories import (
    AnimeRepository,
    EpisodeRepository,
    UserRepository,
    VideoRepository,
    VipRepository,
)
from database.repositories.admin_repository import AdminRepository
from database.repositories.achievement_repository import AchievementRepository
from database.repositories.collection_repository import CollectionRepository
from database.repositories.economy_repository import EconomyRepository
from database.repositories.interaction_repository import (
    FavoriteRepository,
    HistoryRepository,
    WatchlistRepository,
)
from database.repositories.promo_repository import PromoRepository
from database.repositories.referral_repository import ReferralRepository
from database.repositories.schedule_repository import ScheduleRepository
from database.repositories.character_repository import CharacterRepository
from database.repositories.media_gallery_repository import MediaGalleryRepository
from database.repositories.news_repository import NewsRepository
from database.repositories.poll_repository import PollRepository, QuizRepository
from database.repositories.alias_repository import AliasRepository
from database.repositories.rating_repository import (
    CommentRepository,
    NotificationRepository,
    RatingRepository,
)
from database.repositories.search_history_repository import SearchHistoryRepository
from database.repositories.request_repository import AnimeRequestRepository, BugReportRepository
from services.personal_stats_service import PersonalStatsService
from services.request_service import AnimeRequestService, BugReportService
from services.achievement_service import AchievementService
from services.admin_service import AdminService
from services.ai_service import AIService
from services.analytics_service import AnalyticsService
from services.anime_service import AnimeService
from services.audit_log_service import AuditLogService
from services.backup_service import BackupService
from services.audience_service import AudienceService
from services.broadcast_service import BroadcastService
from services.character_service import CharacterService
from services.collection_service import CollectionService
from services.economy_service import EconomyService
from services.favorite_service import FavoriteService
from services.health_service import HealthService
from services.history_service import HistoryService
from services.list_cache_service import ListCacheService
from services.maintenance_service import MaintenanceService
from services.news_service import NewsService
from services.notification_service import NotificationService
from services.permission_service import PermissionService
from services.poll_service import PollService, QuizService
from services.promo_service import PromoService
from services.rating_service import CommentService, RatingService
from services.recommendation_service import RecommendationService
from services.referral_service import ReferralService
from services.schedule_service import ScheduleService
from services.search_service import SearchService
from services.stats_service import StatsService
from services.subscription_service import SubscriptionService
from services.user_service import UserService
from services.vip_service import VipService
from services.watchlist_service import WatchlistService


@dataclass
class Container:
    settings: Settings
    manager: JsonManager

    users: UserRepository
    animes: AnimeRepository
    episodes: EpisodeRepository
    videos: VideoRepository
    vips: VipRepository
    favorites: FavoriteRepository
    history: HistoryRepository
    watchlist: WatchlistRepository
    admins: AdminRepository
    collections: CollectionRepository
    achievements: AchievementRepository
    economy: EconomyRepository
    promos: PromoRepository
    referrals: ReferralRepository
    schedule: ScheduleRepository
    characters: CharacterRepository
    media_gallery: MediaGalleryRepository
    news: NewsRepository
    polls: PollRepository
    quizzes: QuizRepository
    ratings: RatingRepository
    comments: CommentRepository
    notifications: NotificationRepository
    aliases: AliasRepository
    search_history: SearchHistoryRepository
    anime_requests: AnimeRequestRepository
    bug_reports: BugReportRepository

    # NOTE: avval bu klass faqat AIService ichida "yashiringan" edi va
    # hech qanday joydan tashqaridan chaqirib bo'lmasdi. Endi handlerlar
    # (rasm/audio/video uchun) uni ``container.gemini_client`` orqali
    # bevosita ishlatishi mumkin.
    gemini_client: GeminiClient

    user_service: UserService
    subscription_service: SubscriptionService
    anime_service: AnimeService
    search_service: SearchService
    favorite_service: FavoriteService
    history_service: HistoryService
    list_cache: ListCacheService
    vip_service: VipService
    permission_service: PermissionService
    audit_service: AuditLogService
    admin_service: AdminService
    broadcast_service: BroadcastService
    audience_service: AudienceService
    stats_service: StatsService
    backup_service: BackupService
    ai_service: AIService
    analytics_service: AnalyticsService
    collection_service: CollectionService
    watchlist_service: WatchlistService
    achievement_service: AchievementService
    economy_service: EconomyService
    promo_service: PromoService
    referral_service: ReferralService
    recommendation_service: RecommendationService
    schedule_service: ScheduleService
    character_service: CharacterService
    news_service: NewsService
    poll_service: PollService
    quiz_service: QuizService
    rating_service: RatingService
    comment_service: CommentService
    notification_service: NotificationService
    maintenance_service: MaintenanceService
    anime_request_service: AnimeRequestService
    bug_report_service: BugReportService
    health_service: HealthService | None = None
    personal_stats_service: PersonalStatsService | None = None


@lru_cache(maxsize=1)
def get_container() -> Container:
    settings = get_settings()
    manager = JsonManager(
        base_dir=settings.json_dir,
        backup_dir=settings.backup_path,
        cache_ttl_seconds=300,
        cache_max_entries=512,
    )

    users = UserRepository(manager)
    animes = AnimeRepository(manager)
    episodes = EpisodeRepository(manager)
    videos = VideoRepository(manager)
    vips = VipRepository(manager)
    favorites = FavoriteRepository(manager)
    history = HistoryRepository(manager)
    watchlist = WatchlistRepository(manager)
    admins = AdminRepository(manager)
    collections = CollectionRepository(manager)
    achievements = AchievementRepository(manager)
    economy = EconomyRepository(manager)
    promos = PromoRepository(manager)
    referrals = ReferralRepository(manager)
    schedule = ScheduleRepository(manager)
    characters = CharacterRepository(manager)
    media_gallery = MediaGalleryRepository(manager)
    news = NewsRepository(manager)
    polls = PollRepository(manager)
    quizzes = QuizRepository(manager)
    ratings = RatingRepository(manager)
    comments = CommentRepository(manager)
    notifications = NotificationRepository(manager)
    aliases = AliasRepository(manager)
    search_history = SearchHistoryRepository(manager)
    anime_requests = AnimeRequestRepository(manager)
    bug_reports = BugReportRepository(manager)

    permission_service = PermissionService(manager, settings)
    audit_service = AuditLogService(manager)
    analytics_service = AnalyticsService(manager)
    vip_service = VipService(vips, settings)

    # GeminiClient endi bitta joyda yaratiladi va ikkala joyga (Container
    # va AIService) bir xil instance sifatida beriladi — shu bilan
    # handlerlar uni ``container.gemini_client`` orqali to'g'ridan-to'g'ri
    # chaqira oladi, AIService esa uni matnli chat uchun ishlatishda davom
    # etadi.
    gemini_client = GeminiClient(settings.gemini_api_key, settings.gemini_model)

    container_instance = Container(
        settings=settings,
        manager=manager,
        users=users,
        animes=animes,
        episodes=episodes,
        videos=videos,
        vips=vips,
        favorites=favorites,
        history=history,
        watchlist=watchlist,
        admins=admins,
        collections=collections,
        achievements=achievements,
        economy=economy,
        promos=promos,
        referrals=referrals,
        schedule=schedule,
        characters=characters,
        media_gallery=media_gallery,
        news=news,
        polls=polls,
        quizzes=quizzes,
        ratings=ratings,
        comments=comments,
        notifications=notifications,
        aliases=aliases,
        search_history=search_history,
        anime_requests=anime_requests,
        bug_reports=bug_reports,
        gemini_client=gemini_client,
        user_service=UserService(users, settings),
        subscription_service=SubscriptionService(manager),
        anime_service=AnimeService(animes, episodes, videos, analytics_service),
        search_service=SearchService(animes, aliases, search_history),
        favorite_service=FavoriteService(favorites),
        history_service=HistoryService(history),
        list_cache=ListCacheService(),
        vip_service=vip_service,
        permission_service=permission_service,
        audit_service=audit_service,
        admin_service=AdminService(admins, users, permission_service, audit_service, manager),
        broadcast_service=BroadcastService(manager, users),
        audience_service=AudienceService(users, vips, favorites, animes),
        stats_service=StatsService(users, animes, vips),
        backup_service=BackupService(manager, settings.json_dir, settings.backup_path),
        ai_service=AIService(
            manager,
            gemini_client,
            animes,
            users,
            daily_limit=CONSTANTS.AI_DAILY_LIMIT,
        ),
        analytics_service=analytics_service,
        collection_service=CollectionService(collections, animes),
        watchlist_service=WatchlistService(watchlist, animes, episodes),
        achievement_service=AchievementService(achievements),
        economy_service=EconomyService(economy, vip_service),
        promo_service=PromoService(promos, vips, economy),
        referral_service=ReferralService(referrals, economy, users),
        recommendation_service=RecommendationService(animes, favorites, history),
        schedule_service=ScheduleService(schedule, animes),
        character_service=CharacterService(characters, media_gallery),
        news_service=NewsService(news),
        poll_service=PollService(polls),
        quiz_service=QuizService(quizzes, economy),
        rating_service=RatingService(ratings, animes),
        comment_service=CommentService(comments),
        notification_service=NotificationService(notifications, users),
        maintenance_service=MaintenanceService(manager),
        anime_request_service=AnimeRequestService(anime_requests),
        bug_report_service=BugReportService(bug_reports),
    )
    container_instance.health_service = HealthService(container_instance)
    container_instance.personal_stats_service = PersonalStatsService(container_instance)
    return container_instance