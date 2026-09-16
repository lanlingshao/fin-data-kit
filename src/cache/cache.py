from typing import Protocol


class ICache(Protocol):
    """
    cache interface protocol
    you can implement this interface to use your own cache, such as redis, memcached, TTLCache, aiocache, etc.
    """
    async def get(self, key: str) -> str:
        pass

    async def set(self, key: str, value: str, expire: int = None) -> None:
        pass
