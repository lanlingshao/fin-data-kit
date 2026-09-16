from dataclasses import dataclass
from typing import Generic

from src.provider.capability import Capability
from src.provider.data_source import Source


@dataclass
class CapabilityPriority:
    priority: int


@dataclass
class CapabilityPriorityConfig(Generic[Source, Capability]):
    capability_priority: dict[Capability, dict[Source, CapabilityPriority]]
