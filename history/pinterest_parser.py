# import urllib.parse

# from asyncio import sleep
# from playwright.async_api import async_playwright, Page, Browser

# class PinterestParserImages:
#     def __init__(
#         self,
#         query: str = 'мотивационные фразы',
#         seconds: int = 60 * 1,
#         browser: Browser = None
#     ):
#         self.query = query
#         self.seconds = seconds
#         self.url = 'https://ru.pinterest.com/resource/BaseSearchResource/get/'
#         self.browser = browser



#     async def get_request(self, page: Page, query: str):
#         async with page.expect_request(self.url) as manager:
#             await page.goto("https://ru.pinterest.com/search/pins/?q={}".format(urllib.parse.quote(query)))
#         return await manager.value

#     async def get_request_page_down(self,page: Page):
#         async with page.expect_request(self.url) as manager:
#             await page.keyboard.press('PageDown')
#             await page.keyboard.press('PageDown')
#             await page.keyboard.press('PageDown')
#             await page.keyboard.press('PageDown')
#             await page.keyboard.press('PageDown')
#         return await manager.value
        

#     async def get_data(self):
#         context = await self.browser.new_context()
#         page = await context.new_page()
#         yield (await self.get_request(page, self.query))
#         while True:
#             yield (await self.get_request_page_down(page))



#     async def images_generator(self):
#         async for request in self.get_data():
#             data =(await (await request.response()).json())['resource_response']['data']['results']
#             for item in data:
#                 images = item['images']
#                 if images:
#                     if 'orig' in images.keys():
#                         yield (images['orig']['url'])
#             await sleep(self.seconds)

import requests
import json

from urllib.parse import quote
url = 'https://ru.pinterest.com/resource/BaseSearchResource/get/'

def get_results(query: str):
    response = requests.get("https://ru.pinterest.com")
    csrftoken = response.cookies.get('csrftoken')

    cookies = {
        'csrftoken': csrftoken,
    }

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'x-csrftoken': csrftoken,
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {
        'source_url': '/search/pins/?q={}&rs=typed'.format(quote(query)),
        'data': {
            "options" : {
                "query": query,
                "scope":"pins"
                }
            }
    }
    while True:
        str_data = {
            'data' : json.dumps(data.copy().pop('data')),
            'source_url' : data['source_url']
        }
        response = requests.post(url=url, headers=headers, cookies=cookies, data=str_data)
        resource = response.json()['resource_response']
        for item in resource['data']['results']:
            yield item['images']['orig']['url']
        bookmark = resource['bookmark']
        data['data']['options'].update({'bookmarks' : [bookmark]})
        



idx = 1
for item in get_results('чау чау'):
    idx += 1
    print (idx)



