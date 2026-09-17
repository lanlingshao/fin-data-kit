import asyncio
import time

from findatakit.client.strategies.base import RequestStrategy


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self._rate = rate
        self._capacity = float(capacity)
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

        self._lock = asyncio.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill

        if elapsed <= 0:
            return

        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._rate,
        )
        self._last_refill = now

    async def acquire(self, tokens: int = 1):
        while True:
            async with self._lock:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                # calculate next available time point
                # 精确计算下次可用时间点
                needed = tokens - self._tokens
                wait_time = needed / self._rate if self._rate > 0 else None

            if wait_time is None:
                raise RuntimeError("rate=0, cannot acquire tokens")

            # 👉 minimum sleep + retry
            # 关键：最小 sleep + 再次尝试
            await asyncio.sleep(wait_time)



class RateLimiter:
    """
    Global stateful rate limiter.
    全局有状态的限流器
    """
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(
        self,
        key: str,
        rate: float,
        capacity: int,
        tokens: int = 1,
    ):
        bucket = await self._get_bucket(key, rate, capacity)
        await bucket.acquire(tokens)

    async def _get_bucket(self, key: str, rate: float, capacity: int) -> TokenBucket:
        # fast path: return bucket if it exists already
        if key in self._buckets:
            return self._buckets[key]

        # initialize lock
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(rate, capacity)

        return self._buckets[key]


class RateLimitStrategy(RequestStrategy):

    def __init__(self):
        self._limiter = RateLimiter()

    def support(self, ctx) -> bool:
        return (
            ctx.config is not None and
            ctx.config.rate_limit is not None
        )

    def _build_key(self, ctx) -> str:
        # 👉 expandable dimensions 可扩展维度
        # current: limit by source 当前仅按 source 限流
        return ctx.source

        # future can: limit by api or user_id
        '''
        return f"{ctx.source}:{ctx.api}"
        return f"{ctx.source}:{ctx.user_id}"
        '''

    async def before_request(self, ctx, request_kwargs: dict):
        cfg = ctx.config.rate_limit
        key = self._build_key(ctx)
        await self._limiter.acquire(
            key=key,
            rate=cfg.rate,
            capacity=cfg.capacity,
        )

    async def after_response(self, ctx, response):
        pass

    async def on_error(self, ctx, error):
        pass
