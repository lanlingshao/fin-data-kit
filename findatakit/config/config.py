from dataclasses import dataclass
from typing import Generic

from findatakit.config.capability_priority_config import CapabilityPriority, build_capability_priority_config
from findatakit.config.source_config import SourceConfig, build_source_config
from findatakit.provider.enum import Capability, Source


@dataclass
class FinDataKitConfig(Generic[Source, Capability]):
    sources: list[SourceConfig]
    capability_priority_config: dict[Capability, dict[Source, CapabilityPriority]]
    provider_path: str
    cookie_expire: int = 3600 * 24 * 60


def build_config(cfg: dict) -> FinDataKitConfig:
    source_configs = [build_source_config(cfg) for cfg in cfg["sources"]]
    capability_priority_config = build_capability_priority_config(cfg["capability_priority"])
    config = FinDataKitConfig(
        sources=source_configs,
        capability_priority_config=capability_priority_config,
        provider_path=cfg["provider_path"],
    )
    if cfg.get('cookie_expire'):
        config.cookie_expire = cfg['cookie_expire']
    return config

