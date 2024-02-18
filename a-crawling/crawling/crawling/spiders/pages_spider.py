from pathlib import Path

import scrapy
from scrapy.crawler import CrawlerProcess
import os

PAGES_COUNT = 100

save_dir_ru = 'pages/ru'
save_dir_en = 'pages/en'
index_file = 'pages/index.txt'

restricted_domains = ['t.me', 'instagram.com', 'vk.com', 'm.vk.com', 'ok.ru', 'youtube.com', 'www.youtube.com',
                      'www.tiktok.com', 'viber.com', 'music.apple.com', 'rutube.ru', 'www.linkedin.com',
                      'linkedin.com', 'apps.apple.com', 'www.apple.com', 'github.com', 'account.ncbi.nlm.nih.gov',
                      'kudago.com', 'www.zoom.com']
restricted_urls = [
    'https://zen.yandex.ru/tolkosprosit',
]
start_urls = [
    'https://cuprum.media/spravochnik/f-mrt',
    'https://cuprum.media/science-answers',
    'https://cuprum.media/columns/nizkouglevodnye-diety',
    'https://cuprum.media/lifestyle/foodstagram',
    'https://cuprum.media/spravochnik/buckwheat-tea-sp',
    'https://meduza.io/feature/2020/03/20/kak-iskat-meditsinskuyu-informatsiyu-vo-vremya-pandemii-i-posle-nee',
]


class PagesSpider(scrapy.Spider):
    name = "pages"
    start_urls = start_urls
    page_counter_ru = 1
    page_counter_en = 1
    page_counter_un = 1

    @classmethod
    def increment_counters(cls, language):
        if language.startswith('ru'):
            cls.page_counter_ru += 1
        elif language.startswith('en'):
            cls.page_counter_en += 1
        else:
            cls.page_counter_un += 1

    def counters_reached(self):
        return ((self.page_counter_ru >= PAGES_COUNT and self.page_counter_en >= PAGES_COUNT)
                or (self.page_counter_ru >= PAGES_COUNT / 2 and self.page_counter_en >= PAGES_COUNT))
        # or (self.page_counter_ru >= PAGES_COUNT and self.page_counter_en >= PAGES_COUNT / 2))

    def total_pages(self):
        return self.page_counter_ru + self.page_counter_en + self.page_counter_un

    def parse(self, response):
        # self.log(f'renett | Visiting url={response.url}')

        url_domain = response.url.split('/')[2]
        if response.url in restricted_urls or url_domain in restricted_domains:
            self.log(f'renett | Skipping URL {response.url} due to block list during parsing')
        else:
            lang_attribute = response.xpath('//html/@lang').get()
            language = lang_attribute.strip()

            if language.startswith('en') or language.startswith('ru'):
                if language.startswith('ru'):
                    filename = f'{self.page_counter_ru}-{response.url.split("/")[-2]}.html'
                    filepath = os.path.join(save_dir_ru, filename)
                else:
                    filename = f'{self.page_counter_en}-{response.url.split("/")[-2]}.html'
                    filepath = os.path.join(save_dir_en, filename)

                #
                with open(filepath, 'wb') as f:
                    f.write(response.body)
                with open(index_file, 'a') as f:
                    f.write(f'{response.url},{language},{filename},{filepath}\n')

                self.log(
                    f'renett | Saved new file with name="{filename}". Language="{language}". Total received {self.total_pages()} pages')

                self.increment_counters(language)

                if self.counters_reached():
                    self.log(f'renett | Received >= {PAGES_COUNT} pages. Crawling stopped!!!')
                    raise scrapy.exceptions.CloseSpider(
                        f'Received needed amount pages. N = {PAGES_COUNT}. Counters info: ru={self.page_counter_ru}, en={self.page_counter_en}, un={self.page_counter_un}')

                next_pages = set(response.css('a::attr(href)').getall() + response.xpath("//a/@href").getall())
                # self.log(f'renett | Next pages from "{response.url}" are = {next_pages}')
                for next_page in next_pages:
                    if (next_page is not None) and (self.page_allowed(next_page)):
                        yield response.follow(next_page, callback=self.parse)

    def page_allowed(self, next_page):
        try:
            url_domain = next_page.split('/')[2]
            if next_page in restricted_urls or url_domain in restricted_domains:
                self.log(f'renett | Skipping URL {next_page} due to block list before visiting it')
                return False
            else:
                return True
        except:
            return True


def create_directories():
    if not os.path.exists(save_dir_ru):
        os.makedirs(save_dir_ru)
    if not os.path.exists(save_dir_en):
        os.makedirs(save_dir_en)


if __name__ == "__main__":
    create_directories()

    process = CrawlerProcess()
    process.crawl(PagesSpider)
    process.start()
