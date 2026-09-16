from collections import defaultdict

from src.findatakit.provider.provider_class_registry import ProviderClassRegistry
from src.findatakit.provider.provider_client import ProviderClientRegistry
from src.findatakit.provider.capability import Capability
from src.findatakit.provider.provider import Provider


class ProviderRegistry:
    def __init__(self):
        self._providers = []
        self._cap_index = defaultdict(list)

    def register(self, provider: Provider):
        self._providers.append(provider)

        for cap in provider.capabilities:
            self._cap_index[cap].append(provider)

    def get_by_capability(self, capability: Capability) -> list[Provider]:
        return self._cap_index.get(capability, [])


def build_provider_registry(provider_client_factory: ProviderClientRegistry):
    registry = ProviderRegistry()

    for cls in ProviderClassRegistry.get_all():
        provider_client = provider_client_factory.get(cls.source)
        # cls is the class of Provider, and it is decorated with @register_provider decorator
        # cls为provider类，通过register_provider装饰器注册到_registry中
        instance = cls(provider_client)
        registry.register(instance)

    return registry
