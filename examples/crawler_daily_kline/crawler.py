import asyncio

from redis.asyncio.client import Redis

from src.findatakit.client.http_client import HttpClient
from src.findatakit.client.strategies.auth import CookieManager, CookieAuthStrategy, AuthAdapter, NoAuthStrategy
from src.findatakit.client.strategies.rate_limit import RateLimitStrategy
from src.findatakit.client.strategies.retry import RetryStrategy
from src.findatakit.config.capability_priority_config import CapabilityPriorityConfig, CapabilityPriority
from src.findatakit.config.source_config import SourceConfig, RetryConfig, RateLimitConfig, CookieAuthConfig
from src.findatakit.provider.enum import CapabilityId, DataSourceId
from src.findatakit.provider.provider_client import ProviderClientRegistry
from src.findatakit.provider.provider_registry import build_provider_registry
from src.findatakit.config.source_config_registry import create_source_config_registry
from src.findatakit.router.health import ProviderHealth
from src.findatakit.router.priority_strategy import PriorityStrategy
from src.findatakit.router.router import ProviderRouter
from src.findatakit.cookie.playwright import PlaywrightTool


class FinDataSource(DataSourceId):
    Xueqiu = "xueqiu"
    Eastmoney = "eastmoney"


class FinCapability(CapabilityId):
    DailyKine = "daily_kline"



# 1. init config
source_confs = [
    SourceConfig(
        source=FinDataSource.Xueqiu,
        headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        },
        retry=RetryConfig(max_retries=2),
        rate_limit=RateLimitConfig(rate=10, capacity=20),
        auth=CookieAuthConfig(
            home_url="https://xueqiu.com",
            cache_key="xueqiu_cookies",
            cookie_num=10,
            refresh_status_code=400,
            refresh_error_code="400016",
        ),
    ),
    SourceConfig(
        source=FinDataSource.Eastmoney,
        retry=RetryConfig(max_retries=2),
        rate_limit=RateLimitConfig(rate=10, capacity=100),
        auth=None,
    )
]

capability_priority_conf = CapabilityPriorityConfig(
    capability_priority={
        FinCapability.DailyKine: {
            FinDataSource.Xueqiu: CapabilityPriority(priority=1),
            FinDataSource.Eastmoney: CapabilityPriority(priority=2),
        }
    }
)




playwright_tool =  PlaywrightTool("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
redis = Redis(host="localhost", port=6379, db=0, password="")

cookie_manager = CookieManager(cookie_provider=playwright_tool, cache=redis)

rate_limiter_strategy = RateLimitStrategy()
retry_strategy = RetryStrategy()
no_auth_strategy = NoAuthStrategy()
cookie_auth_strategy = CookieAuthStrategy(cookie_manager=cookie_manager)
no_auth_adapter = AuthAdapter(auth=no_auth_strategy)
cookie_auth_adapter = AuthAdapter(auth=cookie_auth_strategy)
strategies = [
    rate_limiter_strategy,
    retry_strategy,
    no_auth_adapter,
    cookie_auth_adapter,
]

http_client = HttpClient(strategies=strategies)
source_config_registry = create_source_config_registry(configs=source_confs)
provider_client_factory = ProviderClientRegistry(
    registry=source_config_registry,
    http_client=http_client,
)
provider_registry = build_provider_registry(provider_client_factory=provider_client_factory)
priority_strategy = PriorityStrategy(config=capability_priority_conf)
provider_health = ProviderHealth()
provider_router = ProviderRouter(
    registry=provider_registry,
    strategy=priority_strategy,
    health=provider_health,
)




async def crawl():
    pass

async def main():
    await crawl()


if __name__ == '__main__':
    asyncio.run(main())
