from .cache.cache import Cache
from .client.http_client import HttpClient
from .client.strategies.auth import (
    AuthAdapter,
    CookieAuthStrategy,
    NoAuthStrategy, CookieManager,
)
from .client.strategies.rate_limit import RateLimitStrategy
from .client.strategies.retry import RetryStrategy
from .config.config import FinDataKitConfig
from .config.source_config_registry import create_source_config_registry
from .cookie.cookie_provider import CookieProvider
from .fin_data_kit import FinDataKit
from .provider.auto_import_provider import auto_import_providers
from .provider.provider_client import ProviderClientRegistry
from .provider.provider_registry import build_provider_registry
from .router.health import ProviderHealth
from .router.priority_strategy import PriorityStrategy
from .router.router import ProviderRouter


def create_client(
    config: FinDataKitConfig,
    cookie_provider: CookieProvider | None = None,
    cache: Cache | None = None,
) -> FinDataKit:
    cookie_manager = CookieManager(
        cookie_provider=cookie_provider,
        cache=cache,
    )

    http_client = HttpClient(
        strategies=[
            RateLimitStrategy(),
            RetryStrategy(),
            AuthAdapter(auth=NoAuthStrategy()),
            AuthAdapter(auth=CookieAuthStrategy(cookie_manager=cookie_manager)),
        ]
    )

    source_config_registry = create_source_config_registry(configs=config.sources)

    provider_client_factory = ProviderClientRegistry(
        registry=source_config_registry,
        http_client=http_client,
    )

    auto_import_providers(config.provider_path)

    provider_registry = build_provider_registry(provider_client_factory=provider_client_factory)

    provider_router = ProviderRouter(
        registry=provider_registry,
        strategy=PriorityStrategy(config=config.capability_priority),
        health=ProviderHealth(),
    )

    return FinDataKit(
        router=provider_router,
    )
