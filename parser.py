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

    def get_season(self):
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
        info['season'] = self.get_season()

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


def parser_factory(site, html):
    if site == 'hulu':
        return HuluParser(html)