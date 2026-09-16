from enum import StrEnum
from typing import TypeVar


class DataSourceId(StrEnum):
    pass

Source = TypeVar("Source", bound=DataSourceId)