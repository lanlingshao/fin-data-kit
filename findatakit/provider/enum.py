from enum import StrEnum
from typing import TypeVar


class DataSourceId(StrEnum):
    pass


class CapabilityId(StrEnum):
    pass


Source = TypeVar("Source", bound=DataSourceId)
Capability = TypeVar("Capability", bound=CapabilityId)
