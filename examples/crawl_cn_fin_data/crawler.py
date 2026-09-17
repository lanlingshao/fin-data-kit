import asyncio
from datetime import date

from examples.crawl_cn_fin_data.constant import FinDataSource, FinCapability
from findatakit.bootstrap import create_client
from findatakit.config.capability_priority_config import CapabilityPriorityConfig, CapabilityPriority
from findatakit.config.config import FinDataKitConfig
from findatakit.config.source_config import SourceConfig, RetryConfig, RateLimitConfig, CookieAuthConfig
from findatakit.cookie.playwright import PlaywrightTool

# ------------------------------
# 1. build config
# ------------------------------

# 1.1 build source config
source_confs = [
    SourceConfig(
        source=FinDataSource.Xueqiu,
        headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        },
        retry=RetryConfig(max_retries=2),
        rate_limit=RateLimitConfig(rate=10, capacity=20),
        # xueqiu need cookie to get daily kline
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
        # eastmoney don't need auth to get daily kline
        auth=None,
    ),
    SourceConfig(
        source=FinDataSource.SSEExchange,
        retry=RetryConfig(max_retries=2),
        # sse exchange don't need auth to get stock list
        auth=None,
    )
]

# 1.2 build capability priority config,
#     we can set multiple data source, and set priority to choose the data source
#     the smaller the priority number is, the earlier it is chosen. if two data source have the same priority,
#     the first one is chosen. if the first failed, the second one is chosen.
capability_priority_conf = CapabilityPriorityConfig(
    capability_priority={
        FinCapability.CnDailyKine: {
            FinDataSource.Xueqiu: CapabilityPriority(priority=1),
            FinDataSource.Eastmoney: CapabilityPriority(priority=2),
        }
    }
)

config = FinDataKitConfig(
    sources=source_confs,
    capability_priority=capability_priority_conf,
    provider_path="examples.crawl_cn_fin_data",
)

# ------------------------------
# 2. create client
# ------------------------------

# if you use Mac, use the browser_path below, if you use linux, just set it to None
browser_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cookie_provider =  PlaywrightTool(browser_path)

# here I use no custom cache, default LocalCache is to store the cookies.
# you can use any cache, like redis, memcache, etc.

# cache = Redis(host="localhost", port=6379, db=0, password="")
client = create_client(
    config=config,
    cookie_provider=cookie_provider,
    cache=None,
)


async def crawl():
    # argument is the same of provider method except capability
    # for example, in examples/crawl_daily_kline/provider.py, the method is get_daily_kline
    daily_klines = await client.get(
        FinCapability.CnDailyKine,
        symbol="000001",
        exchange="SZ",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    print(f"daily_klines: {daily_klines[:10]}")

    sse_stocks = await client.get(FinCapability.SSEStockList)
    print(f"sse_stocks: {sse_stocks[:10]}")


if __name__ == '__main__':
    asyncio.run(crawl())
