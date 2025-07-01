from naifeitv_spider.spider import NaifeiTVSpider

if __name__ == '__main__':
    spider = NaifeiTVSpider()
    movies = spider.get_homepage_movies()
    for movie in movies:
        print(f"标题: {movie['title']}")
        print(f"类型: {movie['type']}")
        print(f"评分: {movie['score']}")
        print(f"简介: {movie['desc']}")
        print('-' * 40) 