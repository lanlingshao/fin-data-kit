from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Optional, Union, Generic

from src.findatakit.provider.enum import Source


# In the future, we can add more auth types, like as password auth, etc.
class AuthType(StrEnum):
    NONE = "none"
    COOKIE = "cookie"


@dataclass
class RetryConfig:
    max_retries: int = 0


@dataclass
class RateLimitConfig:
    rate: float = 5
    capacity: int = 10


@dataclass
class BaseAuthConfig:
    type: ClassVar[AuthType]

@dataclass
class CookieAuthConfig(BaseAuthConfig):
    type = AuthType.COOKIE

    home_url: str
    cache_key: str
    cookie_num: int = 20
    refresh_status_code: int = 400
    refresh_error_code: str = "400016"

# In the future, we can add more auth types, like as password auth, etc.
AuthConfig = Union[
    CookieAuthConfig,
]

@dataclass
class MetricsConfig:
    pass


@dataclass
class SourceConfig(Generic[Source]):
    source: Source
    retry: RetryConfig
    rate_limit: RateLimitConfig
    metrics: MetricsConfig | None = None
    headers: dict[str, str] | None = None
    auth: Optional[AuthConfig] = None
