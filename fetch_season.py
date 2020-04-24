import asyncio
from pyppeteer import launch 
import re
import dataset
import database
import crawler
import sys

async def main(site):
    #インスタンス生成
    db = database.Database(site)
    browser = await launch(headless=False)
    page = await browser.newPage()
    season_crawler = crawler.crawler_factory(site, browser, page)

    #シーズン未チェックのドラマを巡回
    dramas = db.get_season_unchecked_dramas()
    for drama in dramas:
        drama_url = drama['url']
        await season_crawler.goto(drama_url)
        if await season_crawler.season_exist():
            # このドラマにシーズン元であることのフラグを立てる
            db.set_season_origin_flag(drama_url)
            season_urls = await season_crawler.get_season_urls()
            for season_url in season_urls:
                # シーズンURLのレコードを作成
                db.insert_season_url(drama_url, season_url)
                # 各シーズンごとに巡回済みフラグを立てる
                db.set_season_checked_flag(season_url)
            
        #各ドラマごとにシーズンクロールの巡回済みフラグを立てる
        db.set_season_checked_flag(drama_url)

    await season_crawler.browser.close() # ブラウザーを終了する。

if __name__ == '__main__':
    site = sys.argv[1:][0]
    asyncio.run(main(site))