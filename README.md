# fin-data-kit

`fin-data-kit` is an asynchronous framework for collecting financial data. Callers only need to declare the capabilities they require. The framework selects data sources according to configuration, limits request rates, and automatically retries failed requests or falls back to another source.

## Features

- Configuration-driven: retries, rate limits, headers, authentication, and data-source priorities are declared through configuration.
- Pluggable data sources: register providers with `@register_provider`; the configured package is scanned automatically at startup.
- Primary and fallback sources: one capability can be implemented by multiple providers, which are called by priority with automatic fallback on failure.
- Proactive rate limiting: a token bucket is maintained per data source to control request rates and bursts.
- Automatic retries: failed requests are retried with exponential backoff and random jitter.
- Automatic Cookie management: cached cookies are used first and refreshed when missing or authentication fails.
- Fully asynchronous: HTTP requests, rate limiting, retries, and provider interfaces all use `async/await`.

## Installation

The project requires Python 3.12 or later and recommends [uv](https://docs.astral.sh/uv/).

```bash
git clone <repository-url>
cd fin-data-kit
uv sync
```

The Chinese financial data example also uses pandas:

```bash
uv add pandas
```

If Playwright is used to obtain cookies, install its browser binaries:

```bash
uv run playwright install chromium
```

## Quick Start

The Chinese financial data example is located in `examples/crawl_cn_fin_data`. 

run:

```bash
uv run python -m examples.crawl_cn_fin_data.crawler
```

Application code does not need to know which data source is ultimately selected:

```python
daily_klines = await client.get(
    FinCapability.CnDailyKine,
    symbol="000001",
    exchange="SZ",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31),
)
```

## Configure Data Sources and Routing

Each enabled data source has a corresponding `SourceConfig`. The `retry`, `rate_limit`, `headers`, and `auth` options are all optional.

```python
from findatakit import (
    CapabilityPriority, CapabilityPriorityConfig,
)
from findatakit import FinDataKitConfig
from findatakit import (
    RateLimitConfig, RetryConfig, SourceConfig,
)

source_configs = [
    SourceConfig(
        source=FinDataSource.Xueqiu,
        retry=RetryConfig(max_retries=2),
        rate_limit=RateLimitConfig(rate=10, capacity=20),
        headers={"Referer": "https://xueqiu.com/"},
    ),
    SourceConfig(
        source=FinDataSource.Eastmoney,
        retry=RetryConfig(max_retries=2),
        rate_limit=RateLimitConfig(rate=10, capacity=100),
    ),
]

priority_config = CapabilityPriorityConfig(
    capability_priority={
        FinCapability.CnDailyKine: {
            FinDataSource.Xueqiu: CapabilityPriority(priority=1),
            FinDataSource.Eastmoney: CapabilityPriority(priority=2),
        },
    },
)

config = FinDataKitConfig(
    sources=source_configs,
    capability_priority=priority_config,
    provider_path="examples.crawl_cn_fin_data",
)
```

Lower priority numbers are called first; providers without an explicitly configured priority are placed last. When a provider raises an exception, the router tries the next available provider and marks the failed provider as unhealthy. The default cooldown period is 60 seconds, during which it will not be selected again.

`RateLimitConfig(rate=10, capacity=20)` adds 10 tokens per second and allows up to 20 tokens to accumulate. Each request consumes one token. Rate limiting is shared per data source.

## Create a Client

Use `create_client` to assemble the configuration, cookie provider, and cache. A cache implementation only needs to provide asynchronous `get(name)` and `set(name, value, ex=None)` methods, such as `redis.asyncio.Redis`.

```python
from redis.asyncio import Redis
from findatakit.bootstrap import create_client
from findatakit.cookie.playwright import PlaywrightTool

client = create_client(
    config=config,
    cookie_provider=PlaywrightTool(browser_path=None),
    cache=Redis(host="localhost", port=6379, db=0),
)
```

Only data sources configured with `CookieAuthConfig` actually use the cookie provider and cache.

## Develop a Provider Plugin

A provider declares its data source, capabilities, and handler mapping, then registers itself with the decorator:

```python
from enum import StrEnum
from findatakit.provider.provider import Provider
from findatakit.provider.provider_class_registry import register_provider
from findatakit.provider.provider_client import ProviderClient


class MySource(StrEnum):
    Demo = "demo"


class MyCapability(StrEnum):
    Quote = "quote"


@register_provider
class DemoProvider(Provider):
    source = MySource.Demo
    capabilities = {MyCapability.Quote: "get_quote"}

    def __init__(self, client: ProviderClient):
        self._client = client

    async def get_quote(self, symbol: str) -> dict:
        response = await self._client.get(
            "https://api.example.com/quote", params={"symbol": symbol}
        )
        return response.json()
```

Place the module in the Python package specified by `provider_path`. `create_client` scans that package and its submodules; importing them triggers registration through `@register_provider`. Each provider's `source` must be present in `FinDataKitConfig.sources`, otherwise the provider cannot obtain its data-source configuration.

## Cookie Authentication

Data sources that require an authenticated session can configure `CookieAuthConfig`:

```python
SourceConfig(
    source=FinDataSource.Xueqiu,
    auth=CookieAuthConfig(
        home_url="https://xueqiu.com",
        cache_key="xueqiu_cookies",
        cookie_num=10,
        refresh_status_code=400,
        refresh_error_code="400016",
    ),
)
```

The framework first reads cookies from the cache using `cache_key`; if none are found, it calls the cookie provider. When both the response status code and business error code match the refresh configuration, the framework refreshes the cookies and retries the request.

## Testing

Tests are located in `tests/`. They do not access real data sources and do not require a browser or Redis:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The current test suite covers configuration registration, provider capability indexing, priority-based routing, primary/fallback failover, HTTP retries, header merging, and token-bucket rate limiting.

## Project Structure

```text
src/findatakit/
├── bootstrap.py              # Assemble the client and default strategies
├── client/                   # HTTP client, retry, rate limiting, and auth strategies
├── config/                   # Data-source and priority configuration
├── provider/                 # Provider base class, registration, and client
├── router/                   # Routing, health status, and priority strategy
├── cookie/                   # CookieProvider and Playwright implementation
└── cache/                    # Cache protocol
examples/crawl_cn_fin_data/   # Chinese financial data providers and example
tests/                        # Offline unit tests
```
