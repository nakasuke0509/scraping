import asyncio
from pyppeteer import launch 
from bs4 import BeautifulSoup as bs4
import re
import dataset

async def main(): 
    browser = await launch(headless=False)# デフォルトはヘッドレスモードだが、画面を表示するには次の行のようにする。 # browser = await launch(headless=False) 
    page = await browser.newPage() 

    dramas = get_unchecked_dramas()

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

        #話数が表示されるまで待つ処理(parser)
        episode_number = ''
        episode_div = await page.querySelector('div.series-area')
        if episode_div:
            print('episode_div_exist')
            while True:
                await page.evaluate('window.scrollTo(0,document.body.scrollHeight)')
                element = await page.querySelector(".section-header-title")
                try:
                    await asyncio.sleep(3)
                    episode_number = await page.evaluate('(element) => element.textContent', element)
                    episode_number = re.sub('[^0-9]','', episode_number)
                    if int(episode_number) > 0:
                        print( int(episode_number) )
                        break
                except:
                    print('none episode_number')
        

        # ドラマの詳細情報を取得
        info = {}
        html = await page.content()
        soup = bs4(html, 'html.parser')
        print('title: ', soup.title.string)
        #ドラマID(primary key)
        info['id'] = drama['id']
        #ドラマタイトル
        info['title'] = soup.select_one('div.title-detail > div.title > h2').get_text()
        #話数
        info['episode_number'] = episode_number
        #公開年
        start_year = soup.select_one('div.title-detail > div.meta').get_text()
        info['start_year'] = re.sub('[^0-9]','', start_year)
        #放送局
        info['broadcaster'] = soup.select_one('div.title-detail-header:contains("チャンネル") ~ div').get_text()

        #出演者・監督/演出・原作/脚本の取得ロジック
        staff_lis = soup.select('div.title-detail-header:contains("キャスト/スタッフ") ~ div li')
        staff_dict = {}
        # ループの中でli.listLabelのindexを取得
        # for index, staff_list in enumerate(staff_lists):
        #     if staff_list.get('class') == 'listLabel':
        #         staff_indexes[staff_list.get_text()] = index
        # 

        # liタグをループ
        listlabel = ''
        for staff_li in staff_lis:
            # li.listLabelが回ってくるたびにstaff_dictにkey:[]の形で追加
            if staff_li.has_attr('class') and staff_li['class'][0] == 'listLabel':
                listlabel = staff_li.get_text(strip=True)
                print( listlabel )
                #staff_dict[listlabel] = []
                staff_dict.setdefault(listlabel, [])
                print( staff_dict )
            # それ以外の場合は人物なのでリストに追加
            else:
                staff_dict[listlabel].append(staff_li.get_text(strip=True))
        
        info['casts'] = ','.join( staff_dict['出演者'] )
        info['author'] = ','.join( staff_dict['原作/脚本'] )
        info['screenwriter'] = ','.join( staff_dict['原作/脚本'] )

        # DBにドラマ詳細情報を保存
        update_drama_info(info)
        # 巡回済みフラグを立てる


                    
    await browser.close() # ブラウザーを終了する。


# siteのドラマデータ
# 未巡回のドラマのみ
def get_unchecked_dramas():
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

    #ドラマ詳細未チェックドラマのみSELECT
    dramas = table.find(info_checked_flag=0)
    return dramas

# DBクラス(site名依存)
# 詳細情報取得クロールの巡回済みフラグを立てる
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
    data=dict(id=drama_record['id'], info_checked_flag=1)
    table.update(data, ['id'])

def update_drama_info(info):
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

    # 詳細情報を更新
    table.update(info, ['id'])

if __name__ == '__main__':
    asyncio.run(main())

