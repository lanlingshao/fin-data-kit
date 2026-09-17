
from abc import ABC, abstractmethod

from findatakit.client.context import RequestContext


class RequestStrategy(ABC):
    @abstractmethod
    def support(self, ctx: RequestContext) -> bool:
        pass

    @abstractmethod
    async def before_request(self, ctx: RequestContext, request_kwargs: dict):
        pass

    @abstractmethod
    async def after_response(self, ctx: RequestContext, response):
        pass

    @abstractmethod
    async def on_error(self, ctx: RequestContext, error):
        pass