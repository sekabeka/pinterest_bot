import aiohttp
import asyncio
import os
import re
import requests
import random
import json

from datetime import datetime, time
from typing import Tuple
from dotenv import load_dotenv
from aiogram.types import Message, InputMediaPhoto, URLInputFile
from aiogram.fsm.context import FSMContext

from dotenv import load_dotenv
from urllib.parse import quote

url = 'https://ru.pinterest.com/resource/BaseSearchResource/get/'
token = requests.get('https://ru.pinterest.com').cookies.get('csrftoken')
load_dotenv()


def get_proxy():
    api_key = os.getenv('API_TOKEN')
    response = requests.get("https://proxy6.net/api/{}/getproxy".format(api_key))
    result = []
    for d in response.json()['list'].values():
        result.append(
            "http://{}:{}@{}:{}".format(
                d['user'],
                d['pass'],
                d['host'],
                d['port']
            )
        )
    return result

proxy_list = get_proxy()

async def get_results(session: aiohttp.ClientSession, query: str):
    proxy = random.choice(proxy_list)

    cookies = {
        'csrftoken': token,
    }

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'x-csrftoken': token,
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
        async with session.post(url=url, headers=headers, cookies=cookies, data=str_data, proxy=proxy) as response:
            resource = (await response.json())['resource_response']
        #response = requests.post(url=url, headers=headers, cookies=cookies, data=str_data)
        #resource = response.json()['resource_response']
        for item in resource['data']['results']:
            yield item['images']['orig']['url']
        try:
            bookmark = resource['bookmark']
        except:
            yield None
        data['data']['options'].update({'bookmarks' : [bookmark]})



async def work(query: str, message: Message, session: aiohttp.ClientSession, state: FSMContext, seconds: float = 15 * 60):
    group = []
    async for url in get_results(session, query):
        if url is None:
            await message.answer('По запросу ничего не нашлось 😞\nПопробуйте другую формулировку через /add.')
            await state.clear()
            return

        if len(group) == 10:
            await message.answer_media_group(group)
            await asyncio.sleep(seconds)
            group.clear()

        group.append(
            InputMediaPhoto(media=URLInputFile(url))
        )
            

async def extract_query_and_time(text: str) -> Tuple[time, str]:
    pattern = re.compile(r'(\d+:\d+:\d+)')
    if re.search(pattern, text) is not None:
        try:
            time = datetime.strptime(re.search(pattern, text)[1], '%H:%M:%S').time()
        except:
            return 
        query = re.sub(pattern, '', text).strip()
        return time, query
    return 





