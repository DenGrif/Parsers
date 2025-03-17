import logging
import urllib.parse
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils import selenium_request


class AutoRuParser:
    def __init__(self, make, model, year=None):
        self.make = make
        self.model = model
        self.year = year
        self.base_url = "https://auto.ru"
        self.logger = logging.getLogger(__name__)

    def parse(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        try:
            encoded_make = urllib.parse.quote(self.make.lower())
            encoded_model = urllib.parse.quote(self.model.lower())
            prices = []
            page = 1

            start_year = self.year if self.year else 2000
            end_year = datetime.now().year

            while len(prices) < 100:  # Без ограничения на страницы
                search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
                html = selenium_request(search_url, driver)
                soup = BeautifulSoup(html, "html.parser")

                # Извлечение цен
                new_prices = []
                for item in soup.select(".ListingItem"):
                    name_tag = item.select_one(".ListingItemTitle__link")
                    if not name_tag:
                        self.logger.debug(f"Страница {page}: Объявление без имени")
                        continue

                    name_text = name_tag.get_text(strip=True)

                    # Парсинг года
                    year_tag = item.select_one(".ListingItem__yearBlock .ListingItem__year")
                    if year_tag:
                        try:
                            car_year = int(year_tag.get_text(strip=True))
                            if not (start_year <= car_year <= end_year):
                                self.logger.debug(f"Страница {page}: Год {car_year} вне диапазона")
                                continue
                        except ValueError:
                            self.logger.debug(f"Страница {page}: Ошибка парсинга года")
                            continue

                    # Парсинг цены
                    price_containers = [
                        item.select_one(".ListingItemPrice__content a span"),
                        item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
                        item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span"),
                    ]

                    for price_container in price_containers:
                        if price_container:
                            price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
                            if price_text.startswith("от "):
                                price_text = price_text[3:]
                            try:
                                price = int(price_text)
                                if 100_000 <= price <= 200_000_000:
                                    new_prices.append(price)
                                    self.logger.debug(f"Страница {page}: {name_text}, {car_year}, {price} добавлена")
                                else:
                                    self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                            except ValueError:
                                self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
                            break  # Выход после успешного нахождения цены

                prices.extend(new_prices)
                self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

                # Проверка, если достигли 100 цен
                if len(prices) >= 100:
                    self.logger.info("Достигнуто 100 цен, завершаем парсинг.")
                    break

                # Проверка пагинации
                next_page = soup.select_one(".ListingPagination__next")
                if next_page and "href" in next_page.attrs:
                    page += 1
                    time.sleep(random.uniform(2, 4))  # Задержка для маскировки
                else:
                    self.logger.info("Конец пагинации, завершаем парсинг.")
                    break
        finally:
            driver.quit()  # Гарантированное закрытие WebDriver

        self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")

        # Пометка, если найдено менее 100 цен
        if len(prices) < 100:
            self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")

        return prices[:100]
