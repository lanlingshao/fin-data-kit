from cachetools import TTLCache
import asyncio

from findatakit.cache.cache import Cache


class LocalCache(Cache):
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=3600 * 24)
        self.lock = asyncio.Lock()

    async def get(self, name: str):
        async with self.lock:
            return self.cache.get(name)

    async def set(self, name: str, value: str, ex: int = None):
        async with self.lock:
            self.cache[name] = value
