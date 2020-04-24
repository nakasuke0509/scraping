import asyncio
from pyppeteer import launch 
import database
import crawler
import sys

async def main(site):
    db = database.Database(site)
    browser = await launch(headless=False)
    page = await browser.newPage()
    url_crawler = crawler.crawler_factory(site, browser, page)

    parent_urls = db.get_parent_urls()
    for parent_url in parent_urls:
        # 一覧ページに遷移
        await url_crawler.goto( parent_url['url'] )
        # 一覧ページの最後まで移動
        await url_crawler.crawl_until_page_end()
        # 作品URLを取得
        urls = await url_crawler.get_drama_urls()
        print( urls )
        # 作品URLを保存
        db.insert_urls( urls , parent_url )

    print('finish url crawl')
    await url_crawler.browser.close() # ブラウザーを終了する。

if __name__ == '__main__':
    site = sys.argv[1:][0]
    asyncio.run(main(site))