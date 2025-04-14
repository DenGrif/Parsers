import logging
import re
import urllib.parse
import time
import random
from bs4 import BeautifulSoup
from utils import safe_request, setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

class AvitoParser:
    def __init__(self, make, model, year=None, stop_event=None, found_prices=None, lock=None, limit=100, use_proxy=True):
        self.make = make
        self.model = model
        self.year = year if isinstance(year, list) else [year] if year else []
        self.stop_event = stop_event  # Флаг остановки
        self.found_prices = found_prices  # Общий список цен
        self.lock = lock  # Блокировка для синхронизации
        self.limit = limit  # Сохраняем лимит
        self.use_proxy = use_proxy
        self.base_url = "https://www.avito.ru"

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        page = 1

        if len(self.year) == 2:
            start_year, end_year = self.year
        elif len(self.year) == 1:
            start_year = end_year = self.year[0]
        else:
            logger.error("Неверный формат года. Укажите один год или диапазон.")
            return

        while not self.stop_event.is_set():
            search_url = (
                f"{self.base_url}/moskva/avtomobili/{encoded_make}/{encoded_model}/"
                f"?p={page}&radius=1000&searchRadius=1000"
            )

            response = safe_request(search_url, use_proxy=self.use_proxy, retries=3)
            if not response:
                logger.error(f"Не удалось получить страницу {page}")
                page += 1
                continue

            # Парсим страницу
            soup = BeautifulSoup(response.text, "html.parser")
            logger.info(f"Обрабатываю страницу {page}...")
            new_prices = []

            # Извлекаем объявления
            for item in soup.select(".iva-item-content-OWwoq"):
                name_tag = item.select_one('h3[itemprop="name"]')
                if not name_tag:
                    logger.debug(f"Страница {page}: Объявление без имени")
                    continue

                name_text = name_tag.get_text(strip=True).replace("\xa0", " ")

                # Парсинг года
                year_match = re.search(r'\b(\d{4})\b', name_text)
                if year_match:
                    car_year = int(year_match.group(1))
                    if start_year and end_year and not (start_year <= car_year <= end_year):
                        logger.debug(f"Страница {page}: {name_text}, год {car_year} вне диапазона [{start_year}-{end_year}]")
                        continue
                else:
                    logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
                    continue

                # Парсинг цены
                price_tag = item.select_one(".iva-item-priceStep-TIzu3")
                if price_tag:
                    try:
                        price_text = price_tag.get_text(strip=True).split("₽")[0]
                        price_str = "".join(filter(str.isdigit, price_text))
                        if price_str:
                            price = int(price_str)
                            if 100_000 <= price <= 200_000_000:
                                new_prices.append(price)
                                logger.info(f"Страница {page}: {name_text}, цена {price} добавлена")
                            else:
                                logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                    except ValueError:
                        logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")
                        continue

            # Добавляем новые цены в общий список
            with self.lock:
                self.found_prices.extend(new_prices)
                logger.info(f"Страница {page}: добавлено {len(new_prices)} цен. Всего: {len(self.found_prices)}")
                if len(self.found_prices) >= self.limit:  # Проверяем общий лимит
                    self.stop_event.set()  # Устанавливаем флаг остановки
                    logger.info(f"Достигнут лимит в {len(self.found_prices)} цен. Завершаю парсинг.")
                    return

            # Переход на следующую страницу
            next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
            if next_page and not self.stop_event.is_set():
                page += 1
                time.sleep(random.uniform(1, 3) if self.use_proxy else random.uniform(20, 30))
            else:
                logger.info("Конец пагинации, завершаем парсинг.")
                break

        logger.info(f"Обработано {page} страниц, получено {len(self.found_prices)} цен")
