import logging
from bs4 import BeautifulSoup
import urllib.parse
from utils import get_random_user_agent, selenium_request
import time
import random

class AutoRuParser:
    def __init__(self, make, model):
        self.make = make
        self.model = model
        self.base_url = "https://auto.ru"
        self.logger = logging.getLogger(__name__)
        self.max_pages = 10  # Максимум 10 страниц
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            # Можно добавить ещё User-Agent
        ]

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        prices = []
        page = 1

        while len(prices) < 100 and page <= self.max_pages:
            search_url = (
                f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/"
                f"?page={page}"
            )

            # Получение HTML через Selenium
            html = selenium_request(search_url)
            soup = BeautifulSoup(html, "html.parser")

            # Сохранение отладочного файла
            # with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            #     f.write(html)

            # Извлечение цен
            price_containers = []
            # Тип 1: .ListingItemPrice__content
            for elem in soup.select(".ListingItemPrice__content"):
                price_containers.append(elem)
            # Тип 2: .ListingItemPriceNew__link-cYuLr > span
            for link in soup.select(".ListingItemPriceNew__link-cYuLr"):
                span = link.select_one("span")
                if span:
                    price_containers.append(span)
            # Тип 3: цены со скидкой
            for item in soup.select(".ListingItemPriceNew__content-HAVf2 span"):
                price_containers.append(item)

            for container in price_containers:
                try:
                    price_text = container.get_text(strip=True)
                    price_str = price_text.replace("₽", "").replace("\xa0", "").strip()
                    price = int(price_str)
                    if 100_000 <= price <= 200_000_000:
                        prices.append(price)
                except (ValueError, AttributeError):
                    self.logger.debug(f"Ошибка парсинга: {price_text}")

            self.logger.info(f"Страница {page}: добавлено {len(price_containers)} цен")

            # Проверка пагинации
            next_page = soup.select_one(".ListingPagination__next")
            if next_page and "href" in next_page.attrs:
                page += 1
                time.sleep(random.uniform(2, 4))
            else:
                self.logger.info("Конец пагинации")
                break

        self.logger.info(f"Обработано {page-1} страниц, всего цен: {len(prices)}")
        return prices[:100]
