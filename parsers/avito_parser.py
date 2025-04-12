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
    def __init__(self, make, model, year=None, limit=100, use_proxy=True):
        self.make = make
        self.model = model
        self.year = year if isinstance(year, list) else [year] if year else []
        self.limit = limit
        self.use_proxy = use_proxy
        self.base_url = "https://www.avito.ru"

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        prices = []
        page = 1

        # Определение диапазона годов
        if len(self.year) == 2:
            start_year, end_year = self.year
        elif len(self.year) == 1:
            start_year = end_year = self.year[0]
        else:
            logger.error("Неверный формат года. Укажите один год или диапазон.")
            return []

        while len(prices) < self.limit:
            search_url = (
                f"{self.base_url}/moskva/avtomobili/{encoded_make}/{encoded_model}/"
                f"?p={page}&radius=1000&searchRadius=1000"
            )

            response = safe_request(search_url, use_proxy=self.use_proxy, retries=3)
            if not response:
                logger.error(f"Не удалось получить страницу {page}")
                continue  # Пробуем следующую страницу

            # Парсим страницу
            soup = BeautifulSoup(response.text, "html.parser")
            new_prices = []
            logger.info(f"Обрабатываю страницу {page}...")

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

                # Проверка, если достигли лимита
                if len(prices) + len(new_prices) >= self.limit:
                    prices.extend(new_prices[: self.limit - len(prices)])
                    logger.info(f"Достигнуто {self.limit} цен, завершаем парсинг.")
                    return prices

            prices.extend(new_prices)
            logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

            # Проверка кнопки "Следующая страница"
            next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
            if next_page:
                page += 1
                time.sleep(random.uniform(1, 3) if self.use_proxy else random.uniform(20, 30))
            else:
                logger.info("Конец пагинации, завершаем парсинг.")
                break

        logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")

        # Пометка, если найдено менее заданного лимита цен
        if len(prices) < self.limit:
            logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")

        return prices[:self.limit]



# попытка одного счётчика
# import logging
# import re
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from utils import safe_request, setup_logging
#
# # Настройка логирования
# setup_logging()
# logger = logging.getLogger(__name__)
#
# class AvitoParser:
#     def __init__(self, make, model, year=None, use_proxy=True):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.use_proxy = use_proxy
#         self.base_url = "https://www.avito.ru"
#         self.proxy_fail_count = 0  # Счётчик неудачных попыток с прокси
#
#     def parse(self, collected_prices, collected_prices_lock, stop_event, limit):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1
#
#         # Определение диапазона годов
#         if len(self.year) == 2:
#             start_year, end_year = self.year
#         elif len(self.year) == 1:
#             start_year = end_year = self.year[0]
#         else:
#             logger.error("Неверный формат года. Укажите один год или диапазон.")
#             return []
#
#         while not stop_event.is_set():
#             with collected_prices_lock:
#                 total_collected = collected_prices + len(prices)
#                 logger.debug(f"Проверка перед парсингом страницы {page}: collected_prices={collected_prices}, prices={len(prices)}, total_collected={total_collected}, limit={limit}")
#                 if total_collected >= limit:
#                     logger.info(f"Достигнуто общее количество цен: {limit}. Останавливаем парсинг.")
#                     stop_event.set()
#                     break
#
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/{encoded_make}/{encoded_model}/"
#                 f"?p={page}&radius=1000&searchRadius=1000"
#             )
#             response = safe_request(search_url, use_proxy=self.use_proxy, retries=3)
#             if not response:
#                 logger.error(f"Не удалось получить страницу {page} через прокси.")
#                 if self.use_proxy and self.proxy_fail_count < 3:
#                     # Если мы еще не перешли на собственный IP, пробуем с прокси снова
#                     self.proxy_fail_count += 1
#                     continue  # Пробуем снова с прокси
#                 else:
#                     # Переключаемся на собственный IP
#                     logger.info("Прокси не работают. Переходим на собственный IP.")
#                     self.use_proxy = False
#                     response = safe_request(search_url, use_proxy=self.use_proxy)  # Запрос без прокси
#             if not response:
#                 logger.error(f"Не удалось получить страницу {page} ни через прокси, ни через собственный IP.")
#                 break  # Если и через собственный IP не получилось, завершаем парсинг
#
#             # Парсим страницу
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#             logger.info(f"Обрабатываю страницу {page}...")
#
#             # Извлекаем объявления
#             for item in soup.select(".iva-item-content-OWwoq"):
#                 name_tag = item.select_one('h3[itemprop="name"]')
#                 if not name_tag:
#                     logger.debug(f"Страница {page}: Объявление без имени")
#                     continue
#                 name_text = name_tag.get_text(strip=True).replace("\xa0", " ")
#                 # Парсинг года
#                 year_match = re.search(r'\b(\d{4})\b', name_text)
#                 if year_match:
#                     car_year = int(year_match.group(1))
#                     if start_year and end_year and not (start_year <= car_year <= end_year):
#                         logger.debug(f"Страница {page}: {name_text}, год {car_year} вне диапазона [{start_year}-{end_year}]")
#                         continue
#                 else:
#                     logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
#                     continue
#                 # Парсинг цены
#                 price_tag = item.select_one(".iva-item-priceStep-TIzu3")
#                 if price_tag:
#                     try:
#                         price_text = price_tag.get_text(strip=True).split("₽")[0]
#                         price_str = "".join(filter(str.isdigit, price_text))
#                         if price_str:
#                             price = int(price_str)
#                             if 100_000 <= price <= 200_000_000:
#                                 new_prices.append(price)
#                                 logger.info(f"Страница {page}: {name_text}, цена {price} добавлена")
#                             else:
#                                 logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                     except ValueError:
#                         logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")
#                         continue
#
#             prices.extend(new_prices)
#             logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка кнопки "Следующая страница"
#             next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
#             if next_page:
#                 page += 1
#                 time.sleep(random.uniform(1, 3) if self.use_proxy else random.uniform(20, 30))
#             else:
#                 logger.info("Конец пагинации, завершаем парсинг.")
#                 break
#
#         logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#         # Пометка, если найдено менее заданного лимита цен
#         if len(prices) < limit:
#             logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#         return prices



# import logging
# import re
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from utils import safe_request, setup_logging
#
# # Настройка логирования
# setup_logging()
# logger = logging.getLogger(__name__)
#
# class AvitoParser:
#     def __init__(self, make, model, year=None, limit=100, use_proxy=True):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.limit = limit
#         self.use_proxy = use_proxy
#         self.base_url = "https://www.avito.ru"
#         self.proxy_fail_count = 0  # Счётчик неудачных попыток с прокси
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1
#
#         # Определение диапазона годов
#         if len(self.year) == 2:
#             start_year, end_year = self.year
#         elif len(self.year) == 1:
#             start_year = end_year = self.year[0]
#         else:
#             logger.error("Неверный формат года. Укажите один год или диапазон.")
#             return []
#
#         while len(prices) < self.limit:
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/{encoded_make}/{encoded_model}/"
#                 f"?p={page}&radius=1000&searchRadius=1000"
#             )
#
#             response = safe_request(search_url, use_proxy=self.use_proxy, retries=3)
#             if not response:
#                 logger.error(f"Не удалось получить страницу {page} через прокси.")
#                 if self.use_proxy and self.proxy_fail_count < 3:
#                     # Если мы еще не перешли на собственный IP, пробуем с прокси снова
#                     self.proxy_fail_count += 1
#                     continue  # Пробуем снова с прокси
#                 else:
#                     # Переключаемся на собственный IP
#                     logger.info("Прокси не работают. Переходим на собственный IP.")
#                     self.use_proxy = False
#                     response = safe_request(search_url, use_proxy=self.use_proxy)  # Запрос без прокси
#
#             if not response:
#                 logger.error(f"Не удалось получить страницу {page} ни через прокси, ни через собственный IP.")
#                 break  # Если и через собственный IP не получилось, завершаем парсинг
#
#             # Парсим страницу
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#             logger.info(f"Обрабатываю страницу {page}...")
#
#             # Извлекаем объявления
#             for item in soup.select(".iva-item-content-OWwoq"):
#                 name_tag = item.select_one('h3[itemprop="name"]')
#                 if not name_tag:
#                     logger.debug(f"Страница {page}: Объявление без имени")
#                     continue
#
#                 name_text = name_tag.get_text(strip=True).replace("\xa0", " ")
#
#                 # Парсинг года
#                 year_match = re.search(r'\b(\d{4})\b', name_text)
#                 if year_match:
#                     car_year = int(year_match.group(1))
#                     if start_year and end_year and not (start_year <= car_year <= end_year):
#                         logger.debug(f"Страница {page}: {name_text}, год {car_year} вне диапазона [{start_year}-{end_year}]")
#                         continue
#                 else:
#                     logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
#                     continue
#
#                 # Парсинг цены
#                 price_tag = item.select_one(".iva-item-priceStep-TIzu3")
#                 if price_tag:
#                     try:
#                         price_text = price_tag.get_text(strip=True).split("₽")[0]
#                         price_str = "".join(filter(str.isdigit, price_text))
#                         if price_str:
#                             price = int(price_str)
#                             if 100_000 <= price <= 200_000_000:
#                                 new_prices.append(price)
#                                 logger.info(f"Страница {page}: {name_text}, цена {price} добавлена")
#                             else:
#                                 logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                     except ValueError:
#                         logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")
#                         continue
#
#                 # Проверка, если достигли лимита
#                 if len(prices) + len(new_prices) >= self.limit:
#                     prices.extend(new_prices[: self.limit - len(prices)])
#                     logger.info(f"Достигнуто {self.limit} цен, завершаем парсинг.")
#                     return prices
#
#             prices.extend(new_prices)
#             logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка кнопки "Следующая страница"
#             next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
#             if next_page:
#                 page += 1
#                 time.sleep(random.uniform(1, 3) if self.use_proxy else random.uniform(20, 30))
#             else:
#                 logger.info("Конец пагинации, завершаем парсинг.")
#                 break
#
#         logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         # Пометка, если найдено менее заданного лимита цен111
#         if len(prices) < self.limit:
#             logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:self.limit]



# import logging
# import re
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from utils import safe_request, setup_logging
#
# # Настройка логирования
# setup_logging()
# logger = logging.getLogger(__name__)
#
# class AvitoParser:
#     def __init__(self, make, model, year=None, limit=100, use_proxy=True):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.limit = limit
#         self.use_proxy = use_proxy
#         self.base_url = "https://www.avito.ru"
#         self.proxy_fail_count = 0 # Счётчик неудачных попыток с прокси
#         self._stop_parsing = False  # Флаг для остановки парсинга
#
#     def stop(self):
#         """Метод для внешней остановки парсера"""
#         self._stop_parsing = True
#         logger.info("Получен сигнал остановки парсера")
#
#     def parse(self):
#         if self._stop_parsing:
#             logger.info("Парсер остановлен до начала работы")
#             return []
#
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1
#
#         # Определение диапазона годов
#         if len(self.year) == 2:
#             start_year, end_year = self.year
#         elif len(self.year) == 1:
#             start_year = end_year = self.year[0]
#         else:
#             logger.error("Неверный формат года. Укажите один год или диапазон.")
#             return []
#
#         while len(prices) < self.limit and not self._stop_parsing:
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/{encoded_make}/{encoded_model}/"
#                 f"?p={page}&radius=1000&searchRadius=1000"
#             )
#
#             response = safe_request(search_url, use_proxy=self.use_proxy, retries=3)
#             if not response:
#                 logger.error(f"Не удалось получить страницу {page} через прокси.")
#                 if self.use_proxy and self.proxy_fail_count < 3:
#                     # Если мы еще не перешли на собственный IP, пробуем с прокси снова
#                     self.proxy_fail_count += 1
#                     continue  # Пробуем снова с прокси
#                 else:
#                     # Переключаемся на собственный IP
#                     logger.info("Прокси не работают. Переходим на собственный IP.")
#                     self.use_proxy = False
#                     response = safe_request(search_url, use_proxy=self.use_proxy)
#
#             if not response or self._stop_parsing:
#                 logger.error(f"Не удалось получить страницу {page} ни через прокси, ни через собственный IP.")
#                 break  # Если и через собственный IP не получилось, завершаем парсинг
#
#             # Парсим страницу
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#             logger.info(f"Обрабатываю страницу {page}...")
#
#             # Извлекаем объявления
#             for item in soup.select(".iva-item-content-OWwoq"):
#                 if self._stop_parsing:
#                     break
#
#                 name_tag = item.select_one('h3[itemprop="name"]')
#                 if not name_tag:
#                     logger.debug(f"Страница {page}: Объявление без имени")
#                     continue
#
#                 # очистка
#                 name_text = name_tag.get_text(strip=True).replace("\xa0", " ")
#
#                 # Парсинг года
#                 year_match = re.search(r'\b(\d{4})\b', name_text)
#                 if not year_match:
#                     continue
#
#                 car_year = int(year_match.group(1))
#                 if start_year and end_year and not (start_year <= car_year <= end_year):
#                     logger.debug(f"Страница {page}: {name_text}, год {car_year} вне диапазона [{start_year}-{end_year}]")
#                     continue
#
#                 # Парсинг цены
#                 price_tag = item.select_one(".iva-item-priceStep-TIzu3")
#                 if price_tag:
#                     try:
#                         price_text = price_tag.get_text(strip=True).split("₽")[0]
#                         price_str = "".join(filter(str.isdigit, price_text))
#                         if price_str:
#                             price = int(price_str)
#                             if 100_000 <= price <= 200_000_000:
#                                 new_prices.append(price)
#                                 logger.info(f"Страница {page}: {name_text}, цена {price} добавлена")
#                             else:
#                                 logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                     except ValueError:
#                         logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")
#                         continue
#
#                 # Проверка лимита после каждого объявления
#                 if len(prices) + len(new_prices) >= self.limit:
#                     prices.extend(new_prices[:self.limit - len(prices)])
#                     logger.info(f"Достигнуто {self.limit} цен, завершаем парсинг.")
#                     return prices
#
#             prices.extend(new_prices)
#             logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка кнопки "Следующая страница"
#             next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
#             if not next_page or self._stop_parsing:
#                 break
#
#             page += 1
#             delay = random.uniform(1, 3) if self.use_proxy else random.uniform(20, 30)
#             end_time = time.time() + delay
#             while time.time() < end_time and not self._stop_parsing:
#                 time.sleep(0.1)
#
#         logger.info(f"Завершено. Обработано {page} страниц, собрано {len(prices)} цен")
#
#         # Пометка, если найдено менее заданного лимита цен
#         if len(prices) < self.limit:
#             logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:self.limit]



# import logging
# import re
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from utils import safe_request
#
# class AvitoParser:
#     def __init__(self, make, model, year=None, limit=100, use_proxy=True):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.limit = limit
#         self.use_proxy = use_proxy
#         self.base_url = "https://www.avito.ru"
#         self.proxy_fail_count = 0
#         self.stop_event = None
#         self.logger = logging.getLogger(f"AvitoParser_{make}_{model}")
#
#     def stop(self):
#         """Метод для экстренной остановки"""
#         self._force_stop = True
#         self.logger.info("Получена команда остановки")
#
#     def parse(self):
#         if getattr(self, '_force_stop', False) or (self.stop_event and self.stop_event.is_set()):
#             self.logger.info("Парсер остановлен до начала работы")
#             return []
#
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1
#
#         # Определение диапазона годов
#         if len(self.year) == 2:
#             start_year, end_year = self.year
#         elif len(self.year) == 1:
#             start_year = end_year = self.year[0]
#         else:
#             self.logger.error("Неверный формат года. Укажите один год или диапазон.")
#             return []
#
#         while len(prices) < self.limit:
#             # Проверка флага остановки
#             if getattr(self, '_force_stop', False) or (self.stop_event and self.stop_event.is_set()):
#                 self.logger.info(f"Досрочная остановка. Собрано {len(prices)} цен")
#                 break
#
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/{encoded_make}/{encoded_model}/"
#                 f"?p={page}&radius=1000&searchRadius=1000"
#             )
#
#             try:
#                 response = safe_request(search_url, use_proxy=self.use_proxy, retries=2)
#                 if not response:
#                     if self.stop_event and self.stop_event.is_set():
#                         break
#                     continue
#
#                 # Парсинг страницы
#                 soup = BeautifulSoup(response.text, "html.parser")
#                 new_prices = self._parse_page(soup, page, start_year, end_year)
#                 prices.extend(new_prices)
#
#                 # Проверка лимита после добавления цен
#                 if len(prices) >= self.limit:
#                     break
#
#                 # Проверка пагинации
#                 if not soup.select_one('[data-marker="pagination-button/nextPage"]'):
#                     break
#
#                 page += 1
#                 self._sleep_with_check()
#
#             except Exception as e:
#                 self.logger.error(f"Ошибка парсинга страницы {page}: {str(e)}")
#                 if self.stop_event and self.stop_event.is_set():
#                     break
#
#         return prices[:self.limit]
#
#     def _parse_page(self, soup, page, start_year, end_year):
#         """Парсинг одной страницы"""
#         new_prices = []
#         for item in soup.select(".iva-item-content-OWwoq"):
#             if self.stop_event and self.stop_event.is_set():
#                 break
#
#             # Парсинг названия и года
#             name_tag = item.select_one('h3[itemprop="name"]')
#             if not name_tag:
#                 continue
#
#             name_text = name_tag.get_text(strip=True).replace("\xa0", " ")
#             year_match = re.search(r'\b(\d{4})\b', name_text)
#             if not year_match:
#                 continue
#
#             car_year = int(year_match.group(1))
#             if start_year and end_year and not (start_year <= car_year <= end_year):
#                 continue
#
#             # Парсинг цены
#             price_tag = item.select_one(".iva-item-priceStep-TIzu3")
#             if price_tag:
#                 try:
#                     price_text = price_tag.get_text(strip=True).split("₽")[0]
#                     price_str = "".join(filter(str.isdigit, price_text))
#                     if price_str:
#                         price = int(price_str)
#                         if 100_000 <= price <= 200_000_000:
#                             new_prices.append(price)
#                 except ValueError:
#                     continue
#
#         return new_prices
#
#     def _sleep_with_check(self):
#         """Задержка с проверкой флага остановки"""
#         delay = random.uniform(1, 3) if self.use_proxy else random.uniform(20, 30)
#         end_time = time.time() + delay
#         while time.time() < end_time:
#             if getattr(self, '_force_stop', False) or (self.stop_event and self.stop_event.is_set()):
#                 return
#             time.sleep(0.1)


# последний рабочий






