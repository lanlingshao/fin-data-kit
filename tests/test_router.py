import unittest
from enum import StrEnum

from findatakit import (
    CapabilityPriority,
    CapabilityPriorityConfig,
)
from findatakit.provider.provider import Provider
from findatakit.provider.provider_registry import ProviderRegistry
from findatakit.router.health import ProviderHealth
from findatakit.router.priority_strategy import PriorityStrategy
from findatakit.router.router import ProviderRouter


class Source(StrEnum):
    PRIMARY = "primary"
    BACKUP = "backup"


class Capability(StrEnum):
    QUOTE = "quote"


class FakeProvider(Provider):
    capabilities = {Capability.QUOTE: "get_quote"}

    def __init__(self, source, result=None, error=None):
        self.source = source
        self.result = result
        self.error = error
        self.calls = 0

    async def get_quote(self, symbol):
        self.calls += 1
        if self.error:
            raise self.error
        return {"source": self.source, "symbol": symbol, "value": self.result}


def make_router(*providers):
    registry = ProviderRegistry()
    for provider in providers:
        registry.register(provider)
    priorities = CapabilityPriorityConfig(
        capability_priority={
            Capability.QUOTE: {
                Source.PRIMARY: CapabilityPriority(priority=1),
                Source.BACKUP: CapabilityPriority(priority=2),
            }
        }
    )
    return ProviderRouter(registry, PriorityStrategy(priorities), ProviderHealth())


class TestProviderRouter(unittest.IsolatedAsyncioTestCase):
    async def test_uses_priority_even_when_registration_order_differs(self):
        primary = FakeProvider(Source.PRIMARY, result=1)
        backup = FakeProvider(Source.BACKUP, result=2)
        router = make_router(backup, primary)

        result = await router.call(Capability.QUOTE, "000001")

        self.assertEqual(result["source"], Source.PRIMARY)
        self.assertEqual(primary.calls, 1)
        self.assertEqual(backup.calls, 0)

    async def test_falls_back_and_marks_failed_primary_unhealthy(self):
        primary = FakeProvider(Source.PRIMARY, error=ConnectionError("primary down"))
        backup = FakeProvider(Source.BACKUP, result=2)
        router = make_router(primary, backup)

        result = await router.call(Capability.QUOTE, "000001")
        again = await router.call(Capability.QUOTE, "000002")

        self.assertEqual(result["source"], Source.BACKUP)
        self.assertEqual(again["source"], Source.BACKUP)
        self.assertEqual(primary.calls, 1)
        self.assertEqual(backup.calls, 2)

    async def test_raises_when_no_provider_can_serve_capability(self):
        router = make_router()

        with self.assertRaisesRegex(RuntimeError, "All providers failed: None"):
            await router.call(Capability.QUOTE, "000001")
