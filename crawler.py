import asyncio
from pyppeteer import launch
import re

class Crawler(object):

    def __init__(self, browser, page):
        self.browser = browser
        self.page = page
    
    async def goto(self, url):
        await self.page.goto(url, {'waitUntil': 'domcontentloaded'})
        await asyncio.sleep(3)

    async def get_full_html(self):
        # 最後のページまで読み込み
        await self.crawl_until_page_end()
        # 動的に表示されるDOMを読み込む
        await self.load_dynamic_dom()
        html = await self.page.content()
        return html

    async def load_dynamic_dom(self):
        pass

    async def crawl_until_page_end(self):
        scroll_height1 = await self.page.evaluate('window.pageYOffset')
        await asyncio.sleep(3)

        while True:
            await self.page.evaluate('window.scrollTo(0,document.body.scrollHeight)')
            await asyncio.sleep(3)
            scroll_height2 = await self.page.evaluate('window.pageYOffset')
            if scroll_height1 != scroll_height2:
                scroll_height1 = scroll_height2
                print('now page scrolling and yOffset is {0}'.format(scroll_height2))
            else:
                print('page scroll finish')
                break

    async def season_exist(self):
        pass

    async def get_season_urls(self):
        pass
    
class HuluCrawler(Crawler):

    def __init__(self, browser, page):
        super().__init__(browser, page)

    async def get_drama_urls(self):
        urls = []
        for a in await self.page.querySelectorAll('.title-card-title > a'):
            url = await self.page.evaluate('(e) => e.href', a)
            urls.append( url )
        return urls
    
    async def get_season_drop_down_div(self):
        return await self.page.querySelector('.series-area-header > .dropDown > div')

    async def season_exist(self):
        return await self.get_season_drop_down_div()

    async def get_season_urls(self):
        season_urls = []
        season_drop_down_div  = await self.get_season_drop_down_div()
        await season_drop_down_div.tap()
        await self.page.evaluate('(element) => element.click()', season_drop_down_div)
        await asyncio.sleep(3)

        season_list_tags = await self.page.querySelectorAll('.series-area-header li.sub-menu-item') 
        loop_count = len(season_list_tags)

        drop_down = await self.page.querySelector('.series-area-header > .dropDown')
        # シーズンの数だけ各シーズンのURL取得
        for index in range(loop_count):
            # classがopenか確認
            drop_down_class_list = await self.page.evaluate('(element) => element.classList', drop_down)
            if not ('open' in drop_down_class_list.values() ):
                await self.page.evaluate('(element) => element.click()', season_drop_down_div)
                await asyncio.sleep(3)

            # シーズンDOMが表示まで待機
            await self.page.waitForSelector('.series-area-header li.sub-menu-item')
            # シーズンリストのDOMを再取得
            season_list_tags = await self.page.querySelectorAll('.series-area-header li.sub-menu-item') 
            loop_count = len(season_list_tags)
            # シーズンをクリック
            season_list_span = await season_list_tags[index].querySelector('span')
            #シーズンの表示名を確認
            print(await self.page.evaluate('(element) => element.innerText', season_list_span))
            await self.page.evaluate('(element) => element.click()', season_list_span)
            await asyncio.sleep(3)
            season_url = self.page.url
            season_urls.append(season_url)
        return season_urls
    
    async def load_dynamic_dom(self):
        await self.load_episode_number()

    async def load_episode_number(self):
        episode_number = ''
        episode_div = await self.page.querySelector('div.series-area')
        if episode_div:
            print('episode_div_exist')
            for i in range(3):
                element = await self.page.querySelector(".section-header-title")
                try:
                    await asyncio.sleep(3)
                    episode_number_text = await self.page.evaluate('(element) => element.textContent', element)
                    #episode_number = re.sub('[^0-9]','', episode_number)
                    match_episode_number = re.search(r"[(（](\d+)[)）]", episode_number_text)
                    episode_number = match_episode_number.group(1) if match_episode_number else None
                    if int(episode_number) > 0:
                        print( int(episode_number) )
                        break
                except:
                    print('none episode_number')

class ParaviCrawler(Crawler):

    def __init__(self, browser, page):
        super().__init__(browser, page)

    async def get_drama_urls(self):
        urls = []
        rows = await self.page.querySelectorAll('div.gallery-content > div > div.row')

        for row in rows:
            for a in await row.querySelectorAll('a'):
                url = await self.page.evaluate('(e) => e.href', a)
                urls.append(url)
        return urls

def crawler_factory(site, browser, page):
    if site == 'hulu':
        return HuluCrawler(browser, page)
    elif site == 'paravi':
        return ParaviCrawler(browser, page)

    