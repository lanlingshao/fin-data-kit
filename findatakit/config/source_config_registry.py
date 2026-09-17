from typing import Dict, Generic

from findatakit.config.source_config import SourceConfig
from findatakit.provider.enum import Source


class SourceConfigRegistry(Generic[Source]):
    def __init__(self):
        self._configs: Dict[Source, SourceConfig] = {}

    def register(self, config: SourceConfig):
        if config.source in self._configs:
            raise ValueError(f"Source already registered: {config.source}")

        self._configs[config.source] = config

    def get(self, source: Source) -> SourceConfig:
        try:
            return self._configs[source]
        except KeyError:
            raise ValueError(f"Source not found: {source}")

    def has(self, source: Source) -> bool:
        return source in self._configs

    def remove(self, source: Source):
        self._configs.pop(source, None)

    def list_sources(self) -> list[Source]:
        return list(self._configs.keys())


def create_source_config_registry(configs: list[SourceConfig]) -> SourceConfigRegistry:
    registry = SourceConfigRegistry()
    for cfg in configs:
        registry.register(cfg)
    return registry
