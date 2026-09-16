import asyncio
import json
import random
from abc import ABC, abstractmethod

import httpx

from src.findatakit.cache.cache import Cache
from src.findatakit.client.context import RequestContext
from src.findatakit.client.strategies.base import RequestStrategy
from src.findatakit.client.strategies.retry import RetryException
from src.findatakit.config.source_config import CookieAuthConfig
from src.findatakit.cookie.cookie_provider import CookieProvider


class AuthStrategy(ABC):
    @abstractmethod
    async def apply(self, ctx: RequestContext, request_kwargs: dict):
        pass

    async def on_error(self, ctx: RequestContext, error):
        pass

    async def is_auth_error(self, ctx: RequestContext, response: httpx.Response) -> bool:
        return False


class NoAuthStrategy(AuthStrategy):
    async def apply(self, ctx, request_kwargs):
        pass


class CookieManager:
    """
    Cookie manager

    the purpose of this class is to store the cookies in cache, and refresh them when they expire
    """
    def __init__(self, cookie_provider: CookieProvider, cache: Cache, cookie_expire: int = None):
        self._cookie_provider = cookie_provider
        self._cache = cache
        self._cookie_expire = cookie_expire if cookie_expire else 3600 * 24 * 60

        # 多 key 缓存
        # multi key cache
        self._cookies: dict[str, list[str]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._refresh_locks: dict[str, asyncio.Lock] = {}

    # ========================
    # public interface
    # 对外接口
    # ========================

    async def get_cookie(self, ctx) -> str:
        key = self._build_key(ctx)

        cookies = await self._ensure_cookies(ctx, key)
        return random.choice(cookies)

    async def refresh(self, ctx):
        key = self._build_key(ctx)
        if key not in self._refresh_locks:
            self._refresh_locks[key] = asyncio.Lock()

        async with self._refresh_locks[key]:
            cfg = ctx.config.auth
            cookies = await self._cookie_provider.get_cookies(cfg.home_url, cfg.cookie_num)
            await self._set_cookies(key, cookies)

    # ========================
    # core logic
    # 核心逻辑
    # ========================

    @staticmethod
    def _build_key(ctx) -> str:
        # core: use cache_key to isolate cookies for different requests
        return ctx.config.auth.cache_key

    async def _ensure_cookies(self, ctx, key: str) -> list[str]:
        if key in self._cookies:
            return self._cookies[key]

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            if key not in self._cookies:
                cookies = await self._load_cookies(ctx, key)
                if not cookies:
                    raise RuntimeError(f"failed to initialize cookies: {key}")

                await self._set_cookies(key, cookies)

        return self._cookies[key]

    async def _load_cookies(self, ctx: RequestContext, key: str) -> list[str] | None:
        cfg = ctx.config.auth

        # 1️⃣ try to get cookies from Redis first
        # 先从Redis中获取cookies
        cookies = await self._get_rds_cookies(key)
        if cookies:
            return cookies

        # 2️⃣ try to get cookies from browser
        # 从浏览器中获取cookies
        cookies = await self._cookie_provider.get_cookies(
            cfg.home_url,
            cfg.cookie_num,
        )
        if cookies:
            await self._set_rds_cookies(key, cookies)
            return cookies

        return None

    # ========================
    # storage layer
    # 存储层
    # ========================

    async def _get_rds_cookies(self, key: str) -> list[str] | None:
        cookies_str = await self._cache.get(key)
        if not cookies_str:
            return None
        return json.loads(cookies_str)

    async def _set_rds_cookies(self, key: str, cookies: list[str]):
        await self._cache.set(key, json.dumps(cookies), ex=self._cookie_expire)

    async def _set_cookies(self, key: str, cookies: list[str]):
        self._cookies[key] = cookies
        await self._set_rds_cookies(key, cookies)


class CookieAuthStrategy(AuthStrategy):
    def __init__(self, cookie_manager: CookieManager):
        self._cookie_manager = cookie_manager

    async def is_auth_error(self, ctx: RequestContext, response: httpx.Response) -> bool:
        if response.status_code != ctx.config.auth.refresh_status_code:
            return False
        error_code = response.json().get('error_code')
        return error_code == ctx.config.auth.refresh_error_code

    async def apply(self, ctx: RequestContext, request_kwargs):
        cookie = await self._cookie_manager.get_cookie(ctx)
        headers = request_kwargs.setdefault("headers", {})
        if ctx.config.headers:
            headers.update(ctx.config.headers)
        headers["Cookie"] = cookie

    async def on_error(self, ctx: RequestContext, error):
        # error is a httpx.Response object
        # error是httpx.Response对象
        if ctx.config.auth is None:
            return
        if not isinstance(ctx.config.auth, CookieAuthConfig):
            return
        await self._cookie_manager.refresh(ctx)


class AuthAdapter(RequestStrategy):
    def __init__(self, auth: AuthStrategy):
        self._auth = auth

    def support(self, ctx: RequestContext) -> bool:
        return ctx.config.auth is not None

    async def before_request(self, ctx: RequestContext, request_kwargs):
        await self._auth.apply(ctx, request_kwargs)

    async def after_response(self, ctx: RequestContext, response):
        if await self._auth.is_auth_error(ctx, response):
            await self._auth.on_error(ctx, response)
            raise RetryException("auth failed")

    async def on_error(self, ctx, error):
        await self._auth.on_error(ctx, error)