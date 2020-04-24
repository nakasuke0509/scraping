import asyncio
from pyppeteer import launch 
import re
import dataset
import database
import crawler
import parser
import sys

async def main(site):
    print(site)
    #インスタンス生成
    db = database.Database(site)
    browser = await launch(headless=False)
    page = await browser.newPage()
    info_crawler = crawler.crawler_factory(site, browser, page)

    #詳細情報未チェックのドラマを巡回
    dramas = db.get_unchecked_dramas()
    for drama in dramas:
        # 情報を格納するdict
        info = {}
        info['id'] = drama['id']
        # ページに移動
        drama_url = drama['url']
        await info_crawler.goto(drama_url)
        # 動的に表示されるDOMも表示されたあとにhtml全取得
        html = await info_crawler.get_full_html()
        
        # パーサー処理
        info_parser = parser.parser_factory(site, html)
        # パーサーで取得した情報を格納
        info = info_parser.set_info(info)
        # DBにドラマ詳細情報を保存
        db.update_drama_info(info)
        # 巡回済みフラグを立てる
        db.set_info_checked_flag(drama_url)

    await info_crawler.browser.close() # ブラウザーを終了する。

if __name__ == '__main__':
    site = sys.argv[1:][0]
    asyncio.run(main(site))