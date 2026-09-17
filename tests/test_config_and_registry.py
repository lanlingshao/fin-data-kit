import unittest
from enum import StrEnum

from findatakit import SourceConfig
from findatakit.config.source_config_registry import create_source_config_registry
from findatakit.provider.provider import Provider
from findatakit.provider.provider_registry import ProviderRegistry


class Source(StrEnum):
    PRIMARY = "primary"
    BACKUP = "backup"


class Capability(StrEnum):
    QUOTE = "quote"


class PrimaryProvider(Provider):
    source = Source.PRIMARY
    capabilities = {Capability.QUOTE: "get_quote"}


class TestSourceConfigRegistry(unittest.TestCase):
    def test_register_get_list_and_remove(self):
        primary = SourceConfig(source=Source.PRIMARY)
        backup = SourceConfig(source=Source.BACKUP)
        registry = create_source_config_registry([primary, backup])

        self.assertIs(registry.get(Source.PRIMARY), primary)
        self.assertTrue(registry.has(Source.BACKUP))
        self.assertEqual(registry.list_sources(), [Source.PRIMARY, Source.BACKUP])

        registry.remove(Source.PRIMARY)
        self.assertFalse(registry.has(Source.PRIMARY))
        with self.assertRaisesRegex(ValueError, "Source not found"):
            registry.get(Source.PRIMARY)

    def test_duplicate_source_is_rejected(self):
        duplicate = [
            SourceConfig(source=Source.PRIMARY),
            SourceConfig(source=Source.PRIMARY),
        ]

        with self.assertRaisesRegex(ValueError, "Source already registered"):
            create_source_config_registry(duplicate)


class TestProviderRegistry(unittest.TestCase):
    def test_indexes_provider_by_capability(self):
        provider = PrimaryProvider()
        registry = ProviderRegistry()
        registry.register(provider)

        self.assertEqual(registry.get_by_capability(Capability.QUOTE), [provider])
        self.assertEqual(registry.get_by_capability("missing"), [])
