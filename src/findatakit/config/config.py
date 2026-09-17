from dataclasses import dataclass

from src.findatakit.config.capability_priority_config import CapabilityPriorityConfig
from src.findatakit.config.source_config import SourceConfig


@dataclass
class FinDataKitConfig:
    sources: list[SourceConfig]
    capability_priority: CapabilityPriorityConfig
    provider_path: str
    cookie_expire: int = 3600 * 24 * 60
