from findatakit.config.capability_priority_config import CapabilityPriority
from findatakit.provider.enum import Capability, Source
from findatakit.provider.provider import Provider


class PriorityStrategy:
    def __init__(self, config: dict[Capability, dict[Source, CapabilityPriority]]):
        self._config = config

    def sort(self, providers: list[Provider], capability: Capability) -> list[Provider]:
        priority_map = self._config.get(capability, {})

        # order by priority desc
        # 按 priority 降序排序
        return sorted(
            providers,
            key=lambda p: priority_map[p.source] if p.source in priority_map else 999,
            reverse=True,
        )
