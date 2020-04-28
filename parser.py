import re
from bs4 import BeautifulSoup as bs4

class Parser(object):
    def __init__(self, html):
        self.soup = bs4(html, 'html.parser')

    def get_drama_title(self):
        return ''

    def get_drama_introduction(self):
        return ''

    def get_episode_number(self):
        return ''

    def get_start_year(self):
        return ''

    def get_broadcaster(self):
        return ''
    
    def get_casts(self):
        return ''
    
    def get_author(self):
        return ''

    def get_screenwriter(self):
        return ''

    def get_artist(self):
        return ''

    def get_themesong(self):
        return ''

    def get_season(self):
        return ''

    def get_category(self):
        return ''

    def set_info(self, info):
        info['title'] = self.get_drama_title()
        info['introduction'] = self.get_drama_introduction()
        info['episode_number'] = self.get_episode_number()
        info['start_year'] = self.get_start_year()
        info['broadcaster'] = self.get_broadcaster()
        info['casts'] = self.get_casts()
        info['author'] = self.get_screenwriter()
        info['screenwriter'] = self.get_screenwriter()
        info['artist'] = self.get_artist()
        info['themesong'] = self.get_themesong()
        info['season'] = self.get_season()
        info['category'] = self.get_category()

        return info

class HuluParser(Parser):

    def __init__(self, html):
        self.soup = bs4(html, 'html.parser')

    def get_error_page(self):
        self.soup.select_one('div.error-page')

    def get_drama_title(self):
        title = self.soup.select_one('div.title-detail > div.title > h2').get_text()
        return title

    def get_drama_introduction(self):
        introduction = self.soup.select_one('div.title-detail-header:contains("あらすじ") ~ div').get_text()
        return introduction

    def get_episode_number(self):
        episode_number_text = self.soup.select_one('.section-header-title').get_text()
        match_episode_number = re.search(r"[(（](\d+)[)）]", episode_number_text)
        episode_number = match_episode_number.group(1) if match_episode_number else None
        return episode_number

    def get_start_year(self):
        start_year = self.soup.select_one('div.title-detail > div.meta').get_text()
        start_year = re.sub('[^0-9]','', start_year)
        return start_year

    def get_broadcaster(self):
        broadcaster = self.soup.select_one('div.title-detail-header:contains("チャンネル") ~ div').get_text()
        return broadcaster

    def __get_staff_dict(self):
        staff_lis = self.soup.select('div.title-detail-header:contains("キャスト/スタッフ") ~ div li')
        staff_dict = {}
        # liタグをループ
        listlabel = ''
        for staff_li in staff_lis:
            # li.listLabelが回ってくるたびにstaff_dictにkey:setの形でsetに追加
            if staff_li.has_attr('class') and staff_li['class'][0] == 'listLabel':
                listlabel = staff_li.get_text(strip=True)
                print( listlabel )
                #staff_dict[listlabel] = set()
                staff_dict.setdefault(listlabel, set())
                print( staff_dict )
            # それ以外の場合は人物なのでリストに追加
            else:
                staff_dict[listlabel].add(staff_li.get_text(strip=True))

        return staff_dict
    
    def get_casts(self):
        staff_dict = self.__get_staff_dict()
        casts = ','.join( staff_dict.get('出演者') ) if staff_dict.get('出演者') else '' 
        return casts
    
    def get_author(self):
        staff_dict = self.__get_staff_dict()
        author = ','.join( staff_dict.get('原作/脚本') ) if staff_dict.get('原作/脚本') else ''
        return author

    def get_screenwriter(self):
        staff_dict = self.__get_staff_dict()
        screenwriter = ','.join( staff_dict.get('原作/脚本') ) if staff_dict.get('原作/脚本') else ''
        return screenwriter

    def get_season(self):
        season_div = self.soup.select_one('div.series-area-header > div > div')
        season = season_div.get_text() if season_div else ''
        return season

class ParaviParser(Parser):

    def __init__(self, html):
        self.soup = bs4(html, 'html.parser')

    def get_drama_title(self):
        # シーズンが存在する場合の作品のタイトル
        title = self.soup.select_one('div.title-overview-content > div.title-link > a')
        if not title:
            # シーズンが存在しない場合の作品のタイトル(シーズンがある場合はシーズン名が表記されている)
            title = self.soup.select_one('div.title-overview-content > h3 > div')
        if not title:
            title = self.soup.select_one('p.playable-title')
        title = title.get_text() if title else ''
        return title

    def get_season(self):
        if self.soup.select_one('div.title-overview-content > div.title-link > a'):
            season = self.soup.select_one('div.title-overview-content > h3 > div')
            season = season.get_text() if season else ''
            return season

    def get_drama_introduction(self):
        introduction = self.soup.select_one('div.title-overview-content > div.synopsis')
        introduction = introduction.get_text() if introduction else ''
        return introduction

    def get_episode_number(self):
        episode_number_text = self.soup.select_one('div.meta > span.duration')
        episode_number = re.sub('[^0-9]','', episode_number_text.get_text()) if episode_number_text else '' 
        return episode_number

    def get_start_year(self):
        start_year = self.soup.select_one('div.meta > span.year')
        start_year = re.sub('[^0-9]','', start_year.get_text()) if start_year else ''
        return start_year

    def __get_meta_dict(self):
        meta_lis = self.soup.select('div.meta-details li')
        meta_dict = {}
        # liタグをループ
        listlabel = ''
        for meta_li in meta_lis:
            # li.listLabelが回ってくるたびにstaff_dictにkey:setの形でsetに追加
            if meta_li.has_attr('class') and meta_li['class'][0] == 'listLabel':
                listlabel = meta_li.get_text(strip=True)
                print( listlabel )
                #staff_dict[listlabel] = set()
                meta_dict.setdefault(listlabel, set())
                print( meta_dict )
            else:
                meta_dict[listlabel].add(meta_li.get_text(strip=True))

        return meta_dict
    
    def get_casts(self):
        meta_dict = self.__get_meta_dict()
        casts = ','.join( meta_dict.get('出演') ) if meta_dict.get('出演') else '' 
        return casts
    
    def get_author(self):
        meta_dict = self.__get_meta_dict()
        author = ','.join( meta_dict.get('原作') ) if meta_dict.get('原作') else ''
        return author

    def get_screenwriter(self):
        meta_dict = self.__get_meta_dict()
        screenwriter = ','.join( meta_dict.get('脚本') ) if meta_dict.get('脚本') else ''
        return screenwriter

    def get_artist(self):
        meta_dict = self.__get_meta_dict()
        artist = ','.join( meta_dict.get('音楽') ) if meta_dict.get('音楽') else ''
        return artist

    def get_themesong(self):
        meta_dict = self.__get_meta_dict()
        themesong = ','.join( meta_dict.get('音楽') ) if meta_dict.get('音楽') else ''
        return themesong

    def get_category(self):
        meta_dict = self.__get_meta_dict()
        category = ','.join( meta_dict.get('ジャンル') ) if meta_dict.get('ジャンル') else ''
        return category

def parser_factory(site, html):
    if site == 'hulu':
        return HuluParser(html)
    elif site == 'paravi':
        return ParaviParser(html)