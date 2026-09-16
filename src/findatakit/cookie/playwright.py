from playwright.async_api import async_playwright

from src.findatakit.cookie.cookie_provider import CookieProvider


class PlaywrightTool(CookieProvider):
    """
    linux must use the Chromium browser that is installed by the playwright.
    installation command: uv add playwright && playwright install chromium
    linux 中要使用 playwright 安装的 Chromium 浏览器
    linux 安装 chromium 浏览器需要使用以下命令：uv add playwright && playwright install chromium
    """
    def __init__(self, browser_path: str = None):
        self._browser_path = browser_path

    @classmethod
    def new(cls, conf):
        return cls(conf["executable_path"])

    async def _launch_browser(self, p, headless: bool = True):
        return await p.chromium.launch(
            executable_path=self._browser_path if self._browser_path else None,
            headless=headless,
        )

    async def get_cookies(self, url: str, count: int) -> list[str]:
        cookie_list: list[str] = []

        async with async_playwright() as p:
            browser = await self._launch_browser(p, headless=True)

            for _ in range(count):
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1366, "height": 768},
                )

                page = await context.new_page()

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )

                cookies = await context.cookies()
                cookie_str = "; ".join(
                    f"{c['name']}={c['value']}" for c in cookies
                )
                cookie_list.append(cookie_str)

                await context.close()

            await browser.close()

        return cookie_list
