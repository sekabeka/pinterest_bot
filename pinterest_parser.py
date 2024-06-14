import urllib.parse

from asyncio import sleep
from playwright.async_api import async_playwright, Page

class PinterestParserImages:
    def __init__(
        self,
        query: str = 'мотивационные фразы',
        seconds: int = 60 * 1
    ):
        self.query = query
        self.seconds = seconds
        self.url = 'https://ru.pinterest.com/resource/BaseSearchResource/get/'



    async def get_request(self, page: Page, query: str):
        async with page.expect_request(self.url) as manager:
            await page.goto("https://ru.pinterest.com/search/pins/?q={}".format(urllib.parse.quote(query)))
        return await manager.value

    async def get_request_page_down(self,page: Page):
        async with page.expect_request(self.url) as manager:
            await page.keyboard.press('PageDown')
            await page.keyboard.press('PageDown')
            await page.keyboard.press('PageDown')
            await page.keyboard.press('PageDown')
            await page.keyboard.press('PageDown')
        return await manager.value
        

    async def get_data(self):
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            yield (await self.get_request(page, self.query))
            while True:
                yield (await self.get_request_page_down(page))



    async def images_generator(self):
        async for request in self.get_data():
            data =(await (await request.response()).json())['resource_response']['data']['results']
            for item in data:
                images = item['images']
                if images:
                    if 'orig' in images.keys():
                        yield (images['orig']['url'])
            await sleep(self.seconds)

