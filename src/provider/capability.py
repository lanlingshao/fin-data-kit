from enum import StrEnum
from typing import TypeVar


class CapabilityId(StrEnum):
    pass


Capability = TypeVar("Capability", bound=CapabilityId)