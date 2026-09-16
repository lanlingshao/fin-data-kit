import logging
import traceback

from src.findatakit.provider.enum import Capability
from src.findatakit.provider.provider_registry import ProviderRegistry
from src.findatakit.router.health import ProviderHealth
from src.findatakit.router.priority_strategy import PriorityStrategy

logger = logging.getLogger(__name__)


class ProviderRouter:

    def __init__(self, registry: ProviderRegistry, strategy: PriorityStrategy, health: ProviderHealth):
        self._registry = registry
        self._strategy = strategy
        self._health = health

    async def call(self, capability: Capability, *args, **kwargs):

        providers = self._registry.get_by_capability(capability)
        providers = self._strategy.sort(providers, capability)

        last_error = None
        last_error_traceback = None

        for p in providers:

            if not self._health.is_available(p):
                continue

            try:
                # 不用get的原因是想让直接抛出异常，好在调试的时候就发现问题
                # the reason of not using get is to directly throw exception
                # so that the problem can be discovered during debugging
                method = p.capabilities[capability]
                fn = getattr(p, method)
                return await fn(*args, **kwargs)

            except Exception as e:
                self._health.record_failure(p)
                last_error = e
                last_error_traceback = traceback.format_exc()
                logger.error(f"Provider {p.__class__.__name__} failed: {e}")
                continue

        raise RuntimeError(f"All providers failed: {last_error}\n {last_error_traceback}")
