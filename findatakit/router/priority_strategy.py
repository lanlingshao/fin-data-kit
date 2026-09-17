from findatakit.config.capability_priority_config import CapabilityPriorityConfig
from findatakit.provider.enum import Capability
from findatakit.provider.provider import Provider


class PriorityStrategy:
    def __init__(self, config: CapabilityPriorityConfig):
        self._config = config

    def sort(self, providers: list[Provider], capability: Capability) -> list[Provider]:
        priority_map = self._config.capability_priority.get(capability, {})

        # order by priority asc
        # 按 priority 升序排序
        return sorted(
            providers,
            key=lambda p: priority_map[p.source].priority
            if p.source in priority_map else 999
        )
