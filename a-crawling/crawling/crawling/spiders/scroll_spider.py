from selenium import webdriver
import time
from scrapy.crawler import CrawlerProcess
import scrapy


class ScrollSpider(scrapy.Spider):
    name = 'scroll_spider'
    start_urls = [
        'https://cuprum.media/science-answers',
        'https://cuprum.media/pitanie-cuprum',
    ]

    def __init__(self):
        self.driver = webdriver.Chrome()

    def parse(self, response):
        self.driver.get(response.url)

        time.sleep(3)

        self.scroll_page_to_bottom()

        time.sleep(3)

        html_content = self.driver.page_source

        with open('scrolled_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

    def scroll_page_to_bottom(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(2)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def closed(self, reason):
        self.driver.quit()


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(ScrollSpider)
    process.start()
