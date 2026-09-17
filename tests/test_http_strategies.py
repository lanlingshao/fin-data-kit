import unittest
from enum import StrEnum
from unittest.mock import AsyncMock, patch

import httpx

from findatakit.client.context import RequestContext
from findatakit.client.http_client import HttpClient
from findatakit.client.strategies.rate_limit import RateLimitStrategy, TokenBucket
from findatakit.client.strategies.retry import RetryStrategy
from findatakit import RateLimitConfig, RetryConfig, SourceConfig


class Source(StrEnum):
    TEST = "test"


class TestHttpClient(unittest.IsolatedAsyncioTestCase):
    async def test_retries_transient_error_and_merges_headers(self):
        response = httpx.Response(200, json={"ok": True})
        transport = AsyncMock()
        transport.request.side_effect = [httpx.ConnectError("offline"), response]
        client = HttpClient(strategies=[RetryStrategy(base_delay=0, max_delay=0)])
        client._client = transport
        config = SourceConfig(
            source=Source.TEST,
            retry=RetryConfig(max_retries=1),
            headers={"X-Source": "configured", "X-Shared": "config"},
        )

        with patch("findatakit.client.strategies.retry.asyncio.sleep", new=AsyncMock()) as sleep:
            actual = await client.request(
                "GET",
                "https://example.test/quote",
                source=Source.TEST,
                config=config,
                headers={"X-Request": "request", "X-Shared": "request"},
            )

        self.assertIs(actual, response)
        self.assertEqual(transport.request.await_count, 2)
        sleep.assert_awaited_once()
        sent_headers = transport.request.await_args.kwargs["headers"]
        self.assertEqual(sent_headers["X-Request"], "request")
        self.assertEqual(sent_headers["X-Source"], "configured")
        self.assertEqual(sent_headers["X-Shared"], "config")
        self.assertIn("user-agent", sent_headers)

    async def test_stops_after_configured_retry_budget(self):
        transport = AsyncMock()
        error = httpx.ConnectError("offline")
        transport.request.side_effect = error
        client = HttpClient(strategies=[RetryStrategy(base_delay=0, max_delay=0)])
        client._client = transport
        config = SourceConfig(source=Source.TEST, retry=RetryConfig(max_retries=1))

        with patch("findatakit.client.strategies.retry.asyncio.sleep", new=AsyncMock()):
            with self.assertRaises(httpx.ConnectError):
                await client.request("GET", "https://example.test", source=Source.TEST, config=config)

        self.assertEqual(transport.request.await_count, 2)


class TestRateLimiting(unittest.IsolatedAsyncioTestCase):
    async def test_strategy_scopes_rate_limit_by_source(self):
        strategy = RateLimitStrategy()
        strategy._limiter.acquire = AsyncMock()
        config = SourceConfig(source=Source.TEST, rate_limit=RateLimitConfig(rate=2, capacity=3))
        ctx = RequestContext(source=Source.TEST, url="https://example.test", method="GET", config=config)

        await strategy.before_request(ctx, {})

        strategy._limiter.acquire.assert_awaited_once_with(
            key=Source.TEST, rate=2, capacity=3
        )

    async def test_token_bucket_rejects_zero_rate_when_no_token_is_available(self):
        bucket = TokenBucket(rate=0, capacity=1)
        await bucket.acquire()

        with self.assertRaisesRegex(RuntimeError, "rate=0"):
            await bucket.acquire()
