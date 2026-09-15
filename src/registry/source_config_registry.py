from typing import Dict, Generic

from src.config.source_config import (
    AuthType,
    CookieAuthConfig,
    AccountAuthConfig,
    RetryConfig,
    RateLimitConfig,
    AuthConfig,
    SourceConfig,
    MetricsConfig,
)
from src.provider.data_source import Source


class SourceConfigRegistry(Generic[Source]):

    def __init__(self):
        self._configs: Dict[Source, SourceConfig] = {}

    def register(self, config: SourceConfig):
        if config.source in self._configs:
            raise ValueError(f"Source already registered: {config.source}")

        self._configs[config.source] = config

    def get(self, source: Source) -> SourceConfig:
        try:
            return self._configs[source]
        except KeyError:
            raise ValueError(f"Source not found: {source}")

    def has(self, source: Source) -> bool:
        return source in self._configs

    def remove(self, source: Source):
        self._configs.pop(source, None)

    def list_sources(self) -> list[Source]:
        return list(self._configs.keys())


def _build_source_config(cfg: dict) -> SourceConfig:
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

    elif auth_type == AuthType.ACCOUNT:
        return AccountAuthConfig(
            username=cfg["username"],
            password=cfg["password"],
            login_url=cfg["login_url"],
        )

    elif auth_type == AuthType.NONE or auth_type is None:
        return None

    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")


def create_source_config_registry(config: Dict[str, any]) -> SourceConfigRegistry:
    registry = SourceConfigRegistry()

    config_list = config.get("sources", [])

    # 可来自 yaml / json / db
    # can from yaml / json /db
    for cfg in config_list:
        source_config = _build_source_config(cfg)
        registry.register(source_config)

    return registry