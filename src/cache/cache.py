from typing import Protocol


class ICache(Protocol):
    """
    cache interface protocol
    you can implement this interface to use your own cache, such as redis, memcached, TTLCache, aiocache, etc.
    """
    async def get(self, name: str) -> str:
        pass

    async def set(self, name: str, value: str, ex: int = None) -> None:
        pass
