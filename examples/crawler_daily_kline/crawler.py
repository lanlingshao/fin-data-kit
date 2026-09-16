import asyncio

from redis.asyncio.client import Redis

from examples.crawler_daily_kline.constant import FinDataSource, FinCapability, AdjustType
from src.findatakit.bootstrap import create_client
from src.findatakit.config.capability_priority_config import CapabilityPriorityConfig, CapabilityPriority
from src.findatakit.config.config import FinDataKitConfig
from src.findatakit.config.source_config import SourceConfig, RetryConfig, RateLimitConfig, CookieAuthConfig
from src.findatakit.cookie.playwright import PlaywrightTool

# ------------------------------
# 1. build config
# ------------------------------

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

config = FinDataKitConfig(
    sources=source_confs,
    capability_priority=capability_priority_conf,
)

# ------------------------------
# 2. create client
# ------------------------------

# if you use Mac, use the browser_path below, if you use linux, just set it to None
browser_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cookie_provider =  PlaywrightTool(browser_path)

# you can use any cache, like redis, memcache, etc. here I use redis.
cache = Redis(host="localhost", port=6379, db=0, password="")
client = create_client(
    config=config,
    cookie_provider=cookie_provider,
    cache=cache,
)


async def crawl():
    res = await client.get(
        FinCapability.DailyKine,
        symbol="000001.SZ",
        start_date="2023-01-01",
        end_date="2023-01-31",
        adjust=AdjustType.NO,
    )
    print(res)


if __name__ == '__main__':
    asyncio.run(crawl())
