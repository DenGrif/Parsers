import logging
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils import selenium_request_drom
import urllib.parse
import time
import random
from datetime import datetime


class DromParser:
    def __init__(self, make, model, year=None):
        self.make = make
        self.model = model
        self.year = year
        self.base_url = "https://auto.drom.ru"
        self.logger = logging.getLogger(__name__)

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        prices = []
        page = 1

        start_year = self.year if self.year else 2000
        end_year = datetime.now().year

        # Инициализация WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--ignore-certificate-errors")  # Игнорировать ошибки SSL
        options.add_argument("--disable-blink-features=AutomationControlled")  # Обход защиты от ботов
        options.add_argument("--disable-features=SecureDns")  # Отключение защиты DNS
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        try:
            while len(prices) < 100:
                search_url = f"{self.base_url}/{encoded_make}/{encoded_model}/page{page}/" if page > 1 else f"{self.base_url}/{encoded_make}/{encoded_model}/"

                html = selenium_request_drom(search_url, driver)
                if not html:
                    self.logger.error(f"Не удалось получить страницу {page}")
                    break

                soup = BeautifulSoup(html, "html.parser")
                new_prices = []

                # Извлекаем объявления
                for item in soup.select('[data-ftid="bulls-list_bull"]'):
                    name_tag = item.select_one('[data-ftid="bull_title"] h3')
                    if not name_tag:
                        self.logger.debug(f"Страница {page}: Объявление без названия")
                        continue

                    name_text = name_tag.get_text(strip=True)
                    year_match = re.search(r'\b(\d{4})\b', name_text)
                    if year_match:
                        car_year = int(year_match.group(1))
                        if not (start_year <= car_year <= end_year):
                            self.logger.debug(f"Страница {page}: Год {car_year} вне диапазона [{start_year}-{end_year}]")
                            continue
                    else:
                        self.logger.debug(f"Страница {page}: Ошибка парсинга года в {name_text}")
                        continue

                    # Извлечение цены
                    price_tag = item.select_one('[data-ftid="bull_price"]')
                    if not price_tag:
                        self.logger.debug(f"Страница {page}: {name_text} без цены")
                        continue

                    try:
                        price_text = price_tag.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
                        if price_text.startswith("от "):
                            price_text = price_text[3:]
                        price = int("".join(filter(str.isdigit, price_text)))
                        if 100_000 <= price <= 200_000_000:
                            new_prices.append(price)
                            self.logger.debug(f"Страница {page}: {car_year}, {price} добавлена")
                        else:
                            self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                    except ValueError:
                        self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")

                prices.extend(new_prices)
                self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

                # Проверка кнопки "Следующая страница"
                next_page = soup.select_one('[data-ftid="component_pagination-item-next"]')
                if next_page and "href" in next_page.attrs:
                    page += 1
                    time.sleep(random.uniform(10, 15))  # Умеренная задержка
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
