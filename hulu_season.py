import asyncio
from pyppeteer import launch 
from bs4 import BeautifulSoup as bs4
import re
import dataset

async def main(): 
    browser = await launch(headless=False)# デフォルトはヘッドレスモードだが、画面を表示するには次の行のようにする。 # browser = await launch(headless=False) 
    page = await browser.newPage() 

    dramas = get_dramas()

    for drama in dramas:
        #urlごとに詳細情報取得
        #url = 'https://www.hulu.jp/the-walking-dead'
        drama_url = drama['url']
        await page.goto(drama_url, {'waitUntil': 'domcontentloaded'}) 
        await asyncio.sleep(3)
        title = await page.title()
        print( title )
        first_url   = page.url
        print( first_url )

    # 話数が表示されるまで待つ処理(parser)
    # episode_number = ''
    # episode_div = await page.querySelector('div.series-area')
    # if episode_div:
    #     print('episode_div_exist')
    #     while True:
    #         await page.evaluate('window.scrollTo(0,document.body.scrollHeight)')
    #         element = await page.querySelector(".section-header-title")
    #         try:
    #             await asyncio.sleep(3)
    #             episode_number = await page.evaluate('(element) => element.textContent', element)
    #             episode_number = re.sub('[^0-9]','', episode_number)
    #             if int(episode_number) > 0:
    #                 print( int(episode_number) )
    #                 break
    #         except:
    #             print('none episode_number')
    
        #シーズン有りの場合の処理(parser)
        season_drop_down_div = await page.querySelector('.series-area-header > .dropDown > div')
        print( season_drop_down_div )
        if season_drop_down_div:
            print('season_exits')
            #season元のurl (drama.url)
            #drama_url = 'https://www.hulu.jp/the-walking-dead'
            # このドラマにシーズン元であることのフラグを立てる
            set_season_origin_flag(drama_url)

            await season_drop_down_div.tap()
            await page.evaluate('(element) => element.click()', season_drop_down_div)
            await asyncio.sleep(3)

            season_list_tags = await page.querySelectorAll('.series-area-header li.sub-menu-item') 
            loop_count = len(season_list_tags)
            print(loop_count)

            #await page.evaluate('(element) => element.click()', season_drop_down_div)
            #await asyncio.sleep(3)

            drop_down = await page.querySelector('.series-area-header > .dropDown')
            #print( await page.evaluate('(element) => element.classList', drop_down) )
            # シーズンの数だけ各シーズンのURL取得
            for index in range(loop_count):
                
                # classがopenか確認
                drop_down_class_list = await page.evaluate('(element) => element.classList', drop_down)
                print( drop_down_class_list )
                if not ('open' in drop_down_class_list.values() ):
                    await page.evaluate('(element) => element.click()', season_drop_down_div)
                    await asyncio.sleep(3)

                # シーズンDOMが表示まで待機
                await page.waitForSelector('.series-area-header li.sub-menu-item')
                # シーズンリストのDOMを再取得
                season_list_tags = await page.querySelectorAll('.series-area-header li.sub-menu-item') 
                loop_count = len(season_list_tags)
                print(loop_count)
                # シーズンをクリック
                season_list_span = await season_list_tags[index].querySelector('span')
                #シーズンの表示名を確認
                print(await page.evaluate('(element) => element.innerText', season_list_span))
                await page.evaluate('(element) => element.click()', season_list_span)
                await asyncio.sleep(3)
                #await season_list_span.click()

                season_url = page.url
                print( season_url )
                insert_season_url(drama_url, season_url)
                # 各シーズンごとに巡回済みフラグを立てる
                set_season_checked_flag(season_url)
            
        #各ドラマごとにシーズンクロールの巡回済みフラグを立てる
        set_season_checked_flag(drama_url)
        

    #html = await page.content()

    #soup = bs4(html, 'html.parser')
    #print('title: ', soup.title.string)

    await browser.close() # ブラウザーを終了する。


# siteのドラマデータ
def get_dramas():
    # 対象のDBを指定
    DBMS    = 'mysql'
    USER    = 'root'
    PASS    = ''
    HOST    = '127.0.0.1'
    DB      = 'drama_db' 
    TABLE   = 'hulu'
    CHARSET = 'utf8'

    db = dataset.connect('{0}://{1}:{2}@{3}/{4}?charset={5}'.format(DBMS, USER, PASS, HOST, DB, CHARSET))
    table = db[TABLE]

    #シーズンの有無チェックしていないドラマのみSELECT
    dramas = table.find(season_checked_flag=0)
    return dramas

# DBクラス(site名依存)
# ドラマの各シーズンurlを元にドラマレコードを作成
def insert_season_url(drama_url, season_url):
    # 対象のDBを指定
    DBMS    = 'mysql'
    USER    = 'root'
    PASS    = ''
    HOST    = '127.0.0.1'
    DB      = 'drama_db' 
    TABLE   = 'hulu'
    CHARSET = 'utf8'

    db = dataset.connect('{0}://{1}:{2}@{3}/{4}?charset={5}'.format(DBMS, USER, PASS, HOST, DB, CHARSET))
    table = db[TABLE]

    season_record = table.find_one(url=season_url)
    drama_record  = table.find_one(url=drama_url)
    if not season_record:
        data=dict(url=season_url, is_global=drama_record['is_global'], category=drama_record['category'])
        table.insert(data)

# DBクラス(site名依存)
# シーズン元のドラマの場合、フラグを立てる
def set_season_origin_flag(drama_url):
    # 対象のDBを指定
    DBMS    = 'mysql'
    USER    = 'root'
    PASS    = ''
    HOST    = '127.0.0.1'
    DB      = 'drama_db' 
    TABLE   = 'hulu'
    CHARSET = 'utf8'

    db = dataset.connect('{0}://{1}:{2}@{3}/{4}?charset={5}'.format(DBMS, USER, PASS, HOST, DB, CHARSET))
    table = db[TABLE]

    drama_record = table.find_one(url=drama_url)
    data=dict(id=drama_record['id'], season_origin_flag=1)
    table.update(data, ['id'])

# DBクラス(site名依存)
# シーズンクロールの巡回済みフラグを立てる
def set_season_checked_flag(drama_url):
    # 対象のDBを指定
    DBMS    = 'mysql'
    USER    = 'root'
    PASS    = ''
    HOST    = '127.0.0.1'
    DB      = 'drama_db' 
    TABLE   = 'hulu'
    CHARSET = 'utf8'

    db = dataset.connect('{0}://{1}:{2}@{3}/{4}?charset={5}'.format(DBMS, USER, PASS, HOST, DB, CHARSET))
    table = db[TABLE]

    drama_record = table.find_one(url=drama_url)
    data=dict(id=drama_record['id'], season_checked_flag=1)
    table.update(data, ['id'])

if __name__ == '__main__':
    asyncio.run(main())

