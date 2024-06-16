import requests
import json
import aiohttp
import os
import random

from dotenv import load_dotenv
from urllib.parse import quote
url = 'https://ru.pinterest.com/resource/BaseSearchResource/get/'


def get_proxy():
    load_dotenv()
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

async def get_results(query: str, session: aiohttp.ClientSession, csrftoken: str):
    proxy = random.choice(proxy_list)

    # async with session.get("https://ru.pinterest.com", proxy=proxy) as response:
    #     csrftoken = response.cookies.get('csrftoken').value
    #response = requests.get("https://ru.pinterest.com")
    #csrftoken = response.cookies.get('csrftoken').value

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
        async with session.post(url=url, headers=headers, cookies=cookies, data=str_data, proxy=proxy) as response:
            resource = (await response.json())['resource_response']
        #response = requests.post(url=url, headers=headers, cookies=cookies, data=str_data)
        #resource = response.json()['resource_response']
        for item in resource['data']['results']:
            yield item['images']['orig']['url']
        bookmark = resource['bookmark']
        data['data']['options'].update({'bookmarks' : [bookmark]})

