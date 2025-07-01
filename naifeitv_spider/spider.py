import requests
from bs4 import BeautifulSoup

class NaifeiTVSpider:
    BASE_URL = 'https://www.naifeitv.me/'

    def fetch_homepage(self):
        response = requests.get(self.BASE_URL)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            raise Exception(f'Failed to fetch homepage: {response.status_code}')
        return response.text

    def parse_homepage(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        # 解析首页影视信息
        for section in soup.find_all('div', class_='module-items'):  # 适配首页影视列表
            for item in section.find_all('div', class_='module-item'):  # 每个影视条目
                title_tag = item.find('div', class_='module-item-title')
                title = title_tag.text.strip() if title_tag else None
                type_tag = item.find('div', class_='module-item-caption')
                type_ = type_tag.text.strip() if type_tag else None
                score_tag = item.find('div', class_='module-item-score')
                score = score_tag.text.strip() if score_tag else None
                desc_tag = item.find('div', class_='module-item-desc')
                desc = desc_tag.text.strip() if desc_tag else None
                results.append({
                    'title': title,
                    'type': type_,
                    'score': score,
                    'desc': desc
                })
        return results

    def get_homepage_movies(self):
        html = self.fetch_homepage()
        return self.parse_homepage(html)

    def search_movies(self, keyword):
        """
        搜索影片，返回 [{id, title, thumb, desc, score, type}]
        """
        url = f"{self.BASE_URL}search/{keyword}.html"
        response = requests.get(url)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for item in soup.find_all('div', class_='module-search-item'):  # 搜索结果条目
            title_tag = item.find('a', class_='video-name')
            title = title_tag.text.strip() if title_tag else None
            href = title_tag['href'] if title_tag else None
            movie_id = href.strip('/').split('/')[-1].replace('.html', '') if href else None
            thumb_tag = item.find('img')
            thumb = thumb_tag['data-src'] if thumb_tag and thumb_tag.has_attr('data-src') else (thumb_tag['src'] if thumb_tag else None)
            desc_tag = item.find('div', class_='video-info')
            desc = desc_tag.text.strip() if desc_tag else None
            score_tag = item.find('div', class_='video-score')
            score = score_tag.text.strip() if score_tag else None
            type_tag = item.find('div', class_='video-tag')
            type_ = type_tag.text.strip() if type_tag else None
            results.append({
                'id': movie_id,
                'title': title,
                'thumb': thumb,
                'desc': desc,
                'score': score,
                'type': type_
            })
        return results

    def get_movie_detail(self, movie_id):
        """
        获取影片详情，返回 {title, desc, episodes, sources:[{id, name}]}
        """
        url = f"{self.BASE_URL}detail/{movie_id}.html"
        response = requests.get(url)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            return {}
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('div', class_='video-info-header')
        title = title_tag.text.strip() if title_tag else ''
        desc_tag = soup.find('div', class_='video-info-content')
        desc = desc_tag.text.strip() if desc_tag else ''
        # 集数
        episodes = []
        episode_tags = soup.find_all('a', class_='num-tab')
        for ep in episode_tags:
            ep_title = ep.text.strip()
            ep_id = ep['href'].strip('/').split('/')[-1].replace('.html', '')
            episodes.append({'id': ep_id, 'title': ep_title})
        # 片源
        sources = []
        source_tags = soup.find_all('div', class_='module-tab-item')
        for idx, src in enumerate(source_tags):
            src_name = src.text.strip()
            sources.append({'id': str(idx), 'name': src_name})
        return {
            'title': title,
            'desc': desc,
            'episodes': episodes,
            'sources': sources
        }

    def get_play_url(self, movie_id, source_id):
        """
        获取播放链接，返回可用的播放url
        """
        # 这里只做简单拼接，实际应解析页面获取真实播放地址
        url = f"{self.BASE_URL}play/{movie_id}-{source_id}.html"
        return url 