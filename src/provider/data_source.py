from enum import StrEnum
from typing import TypeVar


class DataSource(StrEnum):
    pass

Source = TypeVar("Source", bound=DataSource)