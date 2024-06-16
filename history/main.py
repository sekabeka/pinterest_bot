import urllib.parse

from playwright.sync_api import sync_playwright, Page
json_url = 'https://ru.pinterest.com/resource/BaseSearchResource/get/'


def get_request(page, query):
    with page.expect_request(json_url) as manager:
        page.goto("https://ru.pinterest.com/search/pins/?q={}".format(urllib.parse.quote(query)))
    return manager.value



def get_request_page_down(page: Page):
    with page.expect_request(json_url) as manager:
        page.keyboard.press('PageDown')
        page.keyboard.press('PageDown')
        page.keyboard.press('PageDown')
        page.keyboard.press('PageDown')
        page.keyboard.press('PageDown')
    return manager.value
    

def get_data(query: str = 'мемы'):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        yield get_request(page, query)
        while True:
            yield get_request_page_down(page)


        



import time
for request in get_data():
    data = request.response().json()['resource_response']['data']['results']
    for item in data:
        images = item['images']
        if images:
            if 'orig' in images.keys():
                print (images['orig']['url'])
            else:
                print ('non have images')
    print ('sleeping...')
    time.sleep(30)
