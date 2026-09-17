from findatakit.provider.enum import Capability
from findatakit.router.router import ProviderRouter


class FinDataKit:
    def __init__(
        self,
        router: ProviderRouter,
    ):
        self.provider_router = router

    async def get(self, capability: Capability, **kwargs):
        return await self.provider_router.call(capability, **kwargs)
