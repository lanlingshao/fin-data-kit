from findatakit.provider.enum import Capability, Source


class CapabilityPriority(int):
    pass


def build_capability_priority_config(cfg: dict) -> dict[Capability, dict[Source, CapabilityPriority]]:
    capability_priority_config = {}
    for capability, source_priority_map in cfg.items():
        for source, priority in source_priority_map.items():
            if capability not in capability_priority_config:
                capability_priority_config[capability] = {}
            capability_priority_config[capability][source] = CapabilityPriority(priority)
    return capability_priority_config
