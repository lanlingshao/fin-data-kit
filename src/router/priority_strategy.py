from src.provider.capability import Capability
from src.provider.provider import Provider


class PriorityStrategy:

    def __init__(self, config):
        self._config = config

    def sort(self, providers: list[Provider], capability: Capability) -> list[Provider]:
        priority_map = self._config.get(capability, [])

        # 按priority排序, priority越小越靠前
        return sorted(
            providers,
            key=lambda p: priority_map[p.source]["priority"]
            if p.source in priority_map else 999
        )
