from abc import ABC
from typing import Generic

from src.provider.capability import Capability
from src.provider.data_source import Source


class Provider(ABC, Generic[Source, Capability]):
    source: Source
    # capabilities使用dict的原因是，后续在provider的capabilities的配置中替换method
    capabilities: dict[Capability, str]

    def has(self, capability: Capability) -> bool:
        return capability in self.capabilities
