from abc import ABC
from typing import Generic

from src.provider.capability import Capability
from src.provider.data_source import Source


class Provider(ABC, Generic[Source, Capability]):
    """
    provider of data source 数据源提供器

    capabilities use dict, the purpose is to replace the method in this class
    # capabilities使用dict的原因是，后续在provider的capabilities的配置中替换method
    """
    source: Source
    capabilities: dict[Capability, str]

    def has(self, capability: Capability) -> bool:
        return capability in self.capabilities
