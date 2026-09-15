import logging

import httpx

from src.client.context import RequestContext
from src.client.strategies.base import RequestStrategy
from src.client.strategies.retry import RetryException
from src.config.source_config import SourceConfig

logger = logging.getLogger(__name__)


class HttpClient:

    def __init__(self, http_client: httpx.AsyncClient, strategies: list[RequestStrategy] | None = None):
        self._client = http_client
        self._strategies = strategies or []

    async def request(self, method, url, source: str, config: SourceConfig, **kwargs):
        ctx = RequestContext(source=source, url=url, method=method, config=config)

        while True:
            try:
                # before
                for s in self._strategies:
                    if s.support(ctx):
                        await s.before_request(ctx, kwargs)

                headers = kwargs.get("headers", {})
                headers.update(
                    {
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                    }
                )
                if config.headers is not None:
                    headers.update(config.headers)
                kwargs["headers"] = headers

                # request
                resp = await self._client.request(method, url, **kwargs)

                # after
                for s in self._strategies:
                    if s.support(ctx):
                        await s.after_response(ctx, resp)

                return resp

            except RetryException:
                continue

            except Exception as e:
                ctx.should_retry = False
                for s in self._strategies:
                    if s.support(ctx):
                        await s.on_error(ctx, e)
                if ctx.should_retry:
                    continue
                logger.error(f"request error: {e}")
                raise
