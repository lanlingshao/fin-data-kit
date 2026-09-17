import time

from findatakit.client.context import RequestContext
from findatakit.client.strategies.base import RequestStrategy


class MetricsStrategy(RequestStrategy):
    def support(self, ctx: RequestContext) -> bool:
        return ctx.config is not None and ctx.config.metrics is not None

    async def before_request(self, ctx: RequestContext, request_kwargs: dict):
        ctx.start_time = time.time()

    async def after_response(self, ctx: RequestContext, response):
        duration = time.time() - ctx.start_time
        print(f"[Metrics] {ctx.source} {duration:.3f}s")

    async def on_error(self, ctx: RequestContext, error):
        print(f"[Error] {ctx.source} {error}")