import dataset

class Database:
    """DB連携クラス

    スクレイピングで取得した情報をDBに連携する関数群

    Attributes:
        site (str): 各VODのサイト名
        DBMS (str): 属性の説明
        USER (str): DBユーザー名
        PASS (str): DBパスワード
        HOST (str): DBホスト名
        DB   (str): DB名
        CHARSET (str): 文字コード
    """

    DBMS    = 'mysql'
    USER    = 'root'
    PASS    = ''
    HOST    = '127.0.0.1'
    DB      = 'drama_db'
    CHARSET = 'utf8'

    def __init__(self, site):
        """
        Args:
            site (str): 各VODのサイト名
        """
        self.site = site
        self.db = dataset.connect('{0}://{1}:{2}@{3}/{4}?charset={5}'.format(self.DBMS, self.USER, self.PASS, self.HOST, self.DB, self.CHARSET))

    def table_name(self) -> str:
        """ VODの各siteの作品情報を保存しているテーブル名

        Returns:
            str: 各VODの作品情報を保存するテーブル名(=site))
        """
        table_name = self.site
        return table_name
    
    def url_table_name(self) -> str:
        """ 各siteの作品一覧のURLを保存しているテーブル名

        Returns:
            str: テーブル名(={site}_urls)
        """
        table_name = '{0}_{1}'.format(self.site, 'urls')
        return table_name

    def set_url_table(self) -> 'url_table':
        """ datasetでDB操作をするtable

        Returns:
            url_table: 作品一覧URLを保存するテーブル
        """
        table_name = self.url_table_name()
        url_table = self.db[table_name]
        return url_table

    def set_table(self) -> 'table':
        """ datasetでDB操作をするtable

        Returns:
            table: 作品詳細情報を保存するテーブル
        """
        table_name = self.table_name()
        table = self.db[table_name]
        return table

    def insert_urls(self, urls: list, parent_url: dict) -> 'void':
        """作品詳細ページのURLを保存する
        Args:
            urls (list): 作品詳細ページURLを格納したlist
            parent_urls (dict): url_tableから取得
        """
        table = self.set_table()
        for url in urls:
            record = table.find_one(url=url)
            data=dict(url=url, is_global=parent_url['is_global'], category=parent_url['category'])
            if not record:
                table.insert(data)

    def get_parent_urls(self) -> dict:
        """作品一覧ページのURLをDBから取得
        Returns:
            parent_urls (dict): url_tableから取得
        """
        table = self.set_url_table()
        parent_urls = table.find()
        return parent_urls

    def get_season_unchecked_dramas(self) -> dict:
        """シーズン未チェックの作品を取得

        シーズンを持っているか確認するクロールの巡回フラグが立っていない作品をDBから取得

        Returns:
            dramas (dict): tableから取得
        """
        table = self.set_table()
        dramas = table.find(season_checked_flag=0)
        return dramas

    def insert_season_url(self, drama_url: str, season_url: str, season: str) -> 'void':
        """作品の各シーズンurlを元にレコードを作成

        Args:
            drama_url (str) : 作品詳細URL
            season_url (str) : 作品の持つシーズンのURL
            season (str) : シーズン名
        """
        table = self.set_table()
        season_record = table.find_one(url=season_url)
        drama_record  = table.find_one(url=drama_url)
        if not season_record:
            data=dict(url=season_url, is_global=drama_record['is_global'], category=drama_record['category'], season=season)
            table.insert(data)
        else:
            data=dict(id=season_record['id'], url=season_url, is_global=drama_record['is_global'], category=drama_record['category'], season=season)
            table.update(data, ['id'])

    def set_season_origin_flag(self, drama_url: str) -> 'void':
        """シーズン元のドラマの場合、フラグを立てる

        Args:
            drama_url (str) : 作品詳細URL
        """
        table = self.set_table()
        drama_record = table.find_one(url=drama_url)
        data=dict(id=drama_record['id'], season_origin_flag=1)
        table.update(data, ['id'])

    def set_season_checked_flag(self, drama_url: str):
        """シーズンクロールの巡回済みフラグを立てる

        Args:
            drama_url (str) : 作品詳細URL
        """
        table = self.set_table()
        drama_record = table.find_one(url=drama_url)
        data=dict(id=drama_record['id'], season_checked_flag=1)
        table.update(data, ['id'])

    def get_unchecked_dramas(self) -> dict:
        """詳細情報未取得のドラマのみ

        詳細クロールの巡回フラグが立っていない作品をDBから取得
        ドラマ詳細未チェックドラマかつシーズン元ではないドラマのみSELECT

        Returns:
            dramas (dict): tableから取得
        """
        table = self.set_table()
        dramas = table.find(info_checked_flag=0, season_origin_flag=0)
        return dramas

    def set_info_checked_flag(self, drama_url: str) -> 'void':
        """詳細情報取得クロールの巡回済みフラグを立てる

        Args:
            drama_url (str) : 作品詳細URL
        """
        table = self.set_table()
        drama_record = table.find_one(url=drama_url)
        data=dict(id=drama_record['id'], info_checked_flag=1)
        table.update(data, ['id'])

    def delete_not_exist_drama(self, drama_url: str) -> 'void':
        """404ページのURLのドラマを物理削除

        Args:
            drama_url (str) : 作品詳細URL
        """
        table = self.set_table()
        drama_record = table.find_one(url=drama_url)
        table.delete(id=drama_record['id'])

    def update_drama_info(self, info: dict) -> 'void':
        """作品詳細情報をDBに保存

        作品詳細ページで取得した情報を格納したinfoをDBに保存
        カテゴリーのみ既に保存されているデータがあるので、DBから取り出して整理したのち保存

        Args:
            info (dict) : 作品詳細ページで取得した情報
        """
        table = self.set_table()
        drama_record = table.find_one(id=info['id'])
        info_category_set = set( info['category'].split(',') )
        info_category_set |= set( drama_record['category'].split(',') )
        info['category'] = ','.join(info_category_set)
        table.update(info, ['id'])