from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Optional, Union, Generic

from findatakit.provider.enum import Source


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
    retry: RetryConfig | None = None
    rate_limit: RateLimitConfig | None = None
    metrics: MetricsConfig | None = None
    headers: dict[str, str] | None = None
    auth: Optional[AuthConfig] = None


def build_source_config(cfg: dict) -> SourceConfig:
    return SourceConfig(
        source=cfg["source"],
        retry=_build_retry_config(cfg.get("retry", {})),
        rate_limit=_build_rate_limit_config(cfg.get("rate_limit", {})),
        auth=_build_auth_config(cfg.get("auth")),
        metrics=_build_metrics_config(cfg.get("metrics", {})),
    )


def _build_retry_config(cfg: dict) -> RetryConfig:
    return RetryConfig(
        max_retries=cfg.get("max_retries", 0)
    )


def _build_rate_limit_config(cfg: dict) -> RateLimitConfig:
    return RateLimitConfig(
        rate=cfg.get("rate", 5),
        capacity=cfg.get("capacity", 10),
    )

def _build_metrics_config(cfg: dict) -> MetricsConfig:
    return MetricsConfig()


def _build_auth_config(cfg: dict | None) -> AuthConfig | None:
    if not cfg:
        return None

    auth_type = cfg.get("type")

    if auth_type == AuthType.COOKIE:
        return CookieAuthConfig(
            home_url=cfg["home_url"],
            cache_key=cfg["cache_key"],
            cookie_num=cfg.get("cookie_num", 20),
            refresh_status_code=cfg.get("refresh_status_code", 400),
            refresh_error_code=cfg.get("refresh_error_code", "400016"),
        )
    elif auth_type == AuthType.NONE or auth_type is None:
        return None
    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")
