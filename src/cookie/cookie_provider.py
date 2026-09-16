from typing import Protocol


class CookieProvider(Protocol):
    """
    Cookie provider interface protocol

    you can implement this interface to use your own cookie provider,
    or you can use PlaywrightTool in src/cookie/playwright.py
    """
    async def get_cookies(self, url: str, count: int) -> list[str]:
        ...