from patchright.async_api import Playwright, async_playwright, Browser, Page


class BrowserManager:
    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir="./browser_data",
            channel="chrome",
            headless=False,
            no_viewport=True,
        )
        self.page = await self.browser.new_page()

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_page(self) -> Page:
        if not self.page:
            raise RuntimeError(
                "Browser not properly initialized, call 'start()' first."
            )
        return self.page

    async def get_price(self, url: str, xpath_selector: str) -> str:
        page = await self.get_page()
        await page.goto(url, wait_until="domcontentloaded")
        value = await page.locator(f"xpath={xpath_selector}").inner_text()
        return value
