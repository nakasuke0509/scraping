import asyncio
from pyppeteer import launch 
import re
import dataset
import database

async def main(): 
    db = database.Database('hulu')
    browser = await launch(headless=False)
    page = await browser.newPage() 

    parent_urls = get_parent_urls()
    for parent_url in parent_urls:
        print( parent_url['url'])
    
        await page.goto(parent_url['url'], {'waitUntil': 'domcontentloaded'}) #option {'waitUntil': 'domcontentloaded'}
        await asyncio.sleep(3)

        # 下までクロール処理
        #crawl_until_page_end()
        html1 = await page.content()
        await asyncio.sleep(3)

        while True:
            await page.evaluate('window.scrollTo(0,document.body.scrollHeight)')
            await asyncio.sleep(3)
            html2 = await page.content()
            if html1 != html2:
                html1 = html2
            else:
                break

        await asyncio.sleep(1)
        # 検索結果を表示する
        title = await page.title()
        print( title )

        urls = []
        for a in await page.querySelectorAll('.title-card-title > a'):
            url = await page.evaluate('(e) => e.href', a)
            urls.append( url )

        #insert_urls( urls , parent_url )
        db.insert_urls( urls , parent_url )
        print( urls )

    await browser.close() # ブラウザーを終了する。


# DBクラス(site名依存)
def insert_urls(urls, parent_url):

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

    for url in urls:
        record = table.find_one(url=url)
        data=dict(url=url, is_global=parent_url['is_global'], category=parent_url['category'])
        if not record:   
            table.insert(data)

def get_parent_urls():
    # 対象のDBを指定
    DBMS    = 'mysql'
    USER    = 'root'
    PASS    = ''
    HOST    = '127.0.0.1'
    DB      = 'drama_db' 
    TABLE   = 'hulu_urls'
    CHARSET = 'utf8'

    db = dataset.connect('{0}://{1}:{2}@{3}/{4}?charset={5}'.format(DBMS, USER, PASS, HOST, DB, CHARSET))
    table = db[TABLE]

    parent_urls = table.find()
    return parent_urls


async def crawl_until_page_end():
    html1 = await page.content()

    while true:
        await page.evaluate('window.scrollTo(0,document.body.scrollHeight)')
        sleep(3)
        html2 = await page.content()
        if html1 != html2:
            html1 = html2
        else:
            break
        

if __name__ == '__main__':
    asyncio.run(main())

