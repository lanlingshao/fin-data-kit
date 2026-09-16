from typing import Generic

import httpx

from src.findatakit.client import HttpClient
from src.findatakit.provider.data_source import Source
from src.findatakit.registry.source_config_registry import SourceConfigRegistry


class ProviderClient:
    def __init__(
        self,
        source: Source,
        registry: SourceConfigRegistry,
        http_client: HttpClient,
    ):
        self._source = source
        self._registry = registry
        self._client = http_client

    @property
    def source(self):
        return self._source

    async def request(self, method, url, **kwargs) -> httpx.Response:
        config = self._registry.get(self._source)

        return await self._client.request(
            method,
            url,
            source=self._source,
            config=config,
            **kwargs
        )

    async def get(self, url, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)


class ProviderClientRegistry(Generic[Source]):
    """
    data source client registry(lazy load pattern).
    数据源客户端注册器（懒加载）
    """
    def __init__(self, registry, http_client):
        self._registry = registry
        self._client = http_client
        self._cache: dict[Source, ProviderClient] = {}

    def get(self, source: Source) -> ProviderClient:
        if source not in self._cache:
            self._cache[source] = ProviderClient(
                source,
                self._registry,
                self._client,
            )
        return self._cache[source]