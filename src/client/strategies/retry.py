import asyncio
import random
from abc import ABC

from src.client.context import RequestContext
from src.client.strategies.base import RequestStrategy


class RetryException(Exception):
    pass


class RetryStrategy(RequestStrategy):
    def __init__(
        self,
        max_retries=0,
        base_delay=1,
        max_delay=30,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def support(self, ctx: RequestContext) -> bool:
        return ctx.config is not None and ctx.config.retry is not None

    async def before_request(self, ctx: RequestContext, request_kwargs: dict):
        pass

    async def after_response(self, ctx: RequestContext, response):
        pass

    async def on_error(self, ctx: RequestContext, error):
        # retry 指数退避策略
        # exponential backoff strategy
        max_retries = ctx.config.retry.max_retries if ctx.config.retry else self.max_retries
        if ctx.retry_count >= max_retries:
            raise error

        delay = min(self.base_delay * (2 ** ctx.retry_count), self.max_delay)
        # jitter
        delay *= random.uniform(0.8, 1.2)

        ctx.retry_count += 1
        await asyncio.sleep(delay)
        ctx.should_retry = True
