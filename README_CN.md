# fin-data-kit

`fin-data-kit` 是面向金融数据采集的异步爬虫框架。调用方只需声明所需能力（Capability），框架会依配置选择数据源、限制请求频率，并在失败时自动重试或切换备用数据源。

## 特性

- 配置驱动：重试、限速、请求头、认证和数据源优先级均通过配置声明。
- 数据源插件化：使用 `@register_provider` 注册 Provider，启动时自动扫描指定包。
- 多数据源主备切换：同一能力可由多个 Provider 实现，按优先级调用；失败时自动尝试备用源。
- 主动限速：按数据源维护令牌桶，限制请求频率与突发数。
- 自动重试：请求异常按指数退避并加入随机抖动后重试。
- Cookie 自动管理：优先读取缓存，缺失或认证失败时自动刷新。
- 全链路异步：HTTP、限速、重试和 Provider 接口均使用 async/await。

## 安装

项目要求 Python 3.12+，推荐使用 [uv](https://docs.astral.sh/uv/)。

```bash
git clone <repository-url>
cd fin-data-kit
uv sync
```

中国金融数据示例还使用 pandas：

```bash
uv add pandas
```

如果通过 Playwright 获取 Cookie，需要安装浏览器内核：

```bash
uv run playwright install chromium
```

## 快速开始

仓库中的中国金融数据示例在 `examples/crawl_cn_fin_data`。

运行：

```bash
uv run python -m examples.crawl_cn_fin_data.crawler
```

业务代码无需感知最终选择的数据源：

```python
daily_klines = await client.get(
    FinCapability.CnDailyKine,
    symbol="000001",
    exchange="SZ",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31),
)
```

## 配置数据源与路由

每个启用的数据源对应一份 `SourceConfig`；`retry`、`rate_limit`、`headers` 和 `auth` 都是可选项。

```python
from examples.crawl_cn_fin_data.constant import FinDataSource, FinCapability
from findatakit.config.config import build_config

cfg = {
    "sources": [
        {
            "source": FinDataSource.Xueqiu,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            },
            "retry": {
                "max_retries": 2,
            },
            "rate_limit": {
                "rate": 10,
                "capacity": 20,
            },
            # xueqiu need cookie to get daily kline
            "auth": {
                "type": "cookie",
                "home_url": "https://xueqiu.com",
                "cache_key": "xueqiu_cookies",
                "cookie_num": 10,
                "refresh_status_code": 400,
                "refresh_error_code": "400016",
            },
        },
        {
            "source": FinDataSource.Eastmoney,
            "retry": {
                "max_retries": 3,
            },
            "rate_limit": {
                "rate": 100,
                "capacity": 1000,
            },
            # eastmoney don't need auth to get daily kline
            "auth": None,
        },
        {
            "source": FinDataSource.SSEExchange,
            "retry": {
                "max_retries": 3,
            },
            # sse exchange don't need auth to get stock list
            "auth": None,
        },
    ],
    "capability_priority": {
        FinCapability.CnDailyKine: {
            FinDataSource.Xueqiu: 2,
            FinDataSource.Eastmoney: 1,
        },
    },
    "provider_path": "examples.crawl_cn_fin_data",
}
config = build_config(cfg)
```

优先级数字越大越先调用；未配置优先级的 Provider 排在最后。Provider 抛出异常时，路由器会尝试下一个可用 Provider，并将失败者标记为不健康。默认冷却期为 60 秒，期间不会再次选择它。

`RateLimitConfig(rate=10, capacity=20)` 表示每秒补充 10 个令牌，最多累积 20 个；每个请求消耗一个令牌。限速以数据源为维度共享。

## 创建客户端

使用 `create_client` 组装配置、CookieProvider 和缓存。缓存实现只需提供异步 `get(name)` 和 `set(name, value, ex=None)` 方法，例如 `redis.asyncio.Redis`。

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

只有配置了 `CookieAuthConfig` 的数据源才会实际使用 CookieProvider 和缓存。

## 开发 Provider 插件

Provider 需要声明数据源、能力与处理方法的映射，并通过装饰器注册：

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

将模块放进 `provider_path` 指定的 Python 包中。`create_client` 会扫描该包及其子模块，导入后由 `@register_provider` 完成注册。每个 Provider 的 `source` 必须出现在 `FinDataKitConfig.sources` 中，否则无法取得该数据源的配置。

## Cookie 认证

需要登录态的数据源可配置 `CookieAuthConfig`：

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

框架先按 `cache_key` 从缓存读取 Cookie；未命中时调用 CookieProvider。响应状态码和业务错误码同时匹配刷新配置时，框架会刷新 Cookie 并重新请求。

## 测试

测试位于 `tests/`，不访问真实数据源、不依赖浏览器或 Redis：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

目前覆盖配置注册、Provider 能力索引、优先级路由、主备故障切换、HTTP 重试、请求头合并与令牌桶限速。

## 目录结构

```text
findatakit/
├── bootstrap.py              # 组装客户端和默认策略
├── client/                   # HTTP 客户端、重试、限速、认证策略
├── config/                   # 数据源和优先级配置
├── provider/                 # Provider 基类、注册及客户端
├── router/                   # 路由、健康状态和优先级策略
├── cookie/                   # CookieProvider 与 Playwright 实现
└── cache/                    # 缓存协议
examples/crawl_cn_fin_data/   # 中国金融数据 Provider 和示例
tests/                        # 离线单元测试
```
