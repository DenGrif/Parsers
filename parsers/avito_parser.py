import logging
import re
from bs4 import BeautifulSoup
from utils import get_random_user_agent, safe_request
import urllib.parse
import time
import random


class AvitoParser:
    def __init__(self, make, model, year=None):
        self.make = make
        self.model = model
        self.year = year
        self.base_url = "https://www.avito.ru"
        self.logger = logging.getLogger(__name__)

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        prices = []
        page = 1

        if isinstance(self.year, list):
            if len(self.year) == 1:
                start_year = end_year = self.year[0]
            elif len(self.year) == 2:
                start_year, end_year = self.year
            else:
                self.logger.error("Неверный формат года. Укажите один год или диапазон через тире.")
                return prices
        else:
            start_year = end_year = 2000

        while len(prices) < 100:
            search_url = (
                f"{self.base_url}/moskva/avtomobili/"
                f"{encoded_make}/{encoded_model}/"
                f"?p={page}&radius=1000&searchRadius=1000"
            )
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Upgrade-Insecure-Requests": "1",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0"
            }

            response = safe_request(search_url, headers)  # Отключили прокси
            if not response:
                self.logger.error(f"Не удалось получить страницу {page}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            new_prices = []

            # Извлекаем объявления
            for item in soup.select(".iva-item-content-OWwoq"):
                name_tag = item.select_one('h3[itemprop="name"]')
                if not name_tag:
                    self.logger.debug(f"Страница {page}: Объявление без имени")
                    continue

                name_text = name_tag.get_text(strip=True).replace("\xa0", " ")

                # Извлекаем год выпуска
                year_match = re.search(r'\b(\d{4})\b', name_text)
                if year_match:
                    car_year = int(year_match.group(1))
                    if not (start_year <= car_year <= end_year):
                        self.logger.debug(
                            f"Страница {page}: {name_text}, год {car_year} вне диапазона [{start_year}-{end_year}]"
                        )
                        continue
                else:
                    self.logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
                    continue

                # Извлекаем пробег
                mileage_match = re.search(r'(\d{1,3}(?: \d{3})*)\s*км', name_text)
                mileage = int(mileage_match.group(1).replace(" ", "")) if mileage_match else None

                # Извлекаем цену
                price_tag = item.select_one(".iva-item-priceStep-TIzu3")
                if price_tag:
                    try:
                        price_text = price_tag.get_text(strip=True).split("₽")[0]
                        price_str = "".join(filter(str.isdigit, price_text))
                        if price_str:
                            price = int(price_str)

                            if 100_000 <= price <= 200_000_000:
                                new_prices.append(price)
                                self.logger.debug(
                                    f"Страница {page}: {name_text}, пробег: {mileage if mileage else 'не указан'}, цена {price} добавлена"
                                )
                            else:
                                self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                    except ValueError:
                        self.logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")

            prices.extend(new_prices)
            self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

            # Проверка кнопки "Следующая страница"
            next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
            if next_page:
                page += 1
                time.sleep(random.uniform(20, 35))  # Увеличена задержка
            else:
                self.logger.info("Конец пагинации, завершаем парсинг.")
                break

        self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")

        if len(prices) < 100:
            self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")

        return prices[:100]


# копия с дубликатом:
# import logging
# import re
# from bs4 import BeautifulSoup
# from utils import get_random_user_agent, safe_request
# import urllib.parse
# import time
# import random
#
#
# class AvitoParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year
#         self.base_url = "https://www.avito.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         #seen_ads = set()  # Множество для проверки дубликатов
#         page = 1
#
#         if isinstance(self.year, list):
#             if len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             elif len(self.year) == 2:
#                 start_year, end_year = self.year
#             else:
#                 self.logger.error("Неверный формат года. Укажите один год или диапазон через тире.")
#                 return prices
#         else:
#             start_year = end_year = 2000
#
#         while len(prices) < 100:
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/"
#                 f"{encoded_make}/{encoded_model}/"
#                 f"?p={page}&radius=1000&searchRadius=1000"
#             )
#             headers = {
#                 "User-Agent": get_random_user_agent(),
#                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
#                 "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#                 "Upgrade-Insecure-Requests": "1",
#                 "Connection": "keep-alive",
#                 "Cache-Control": "max-age=0"
#             }
#
#             response = safe_request(search_url, headers)  # Отключили прокси
#             if not response:
#                 self.logger.error(f"Не удалось получить страницу {page}")
#                 break
#
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#
#             # Извлекаем объявления
#             for item in soup.select(".iva-item-content-OWwoq"):
#                 name_tag = item.select_one('h3[itemprop="name"]')
#                 if not name_tag:
#                     self.logger.debug(f"Страница {page}: Объявление без имени")
#                     continue
#
#                 name_text = name_tag.get_text(strip=True).replace("\xa0", " ")
#
#                 # Извлекаем год выпуска
#                 year_match = re.search(r'\b(\d{4})\b', name_text)
#                 if year_match:
#                     car_year = int(year_match.group(1))
#                     if not (start_year <= car_year <= end_year):
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, год {car_year} вне диапазона [{start_year}-{end_year}]"
#                         )
#                         continue
#                 else:
#                     self.logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
#                     continue
#
#                 # Извлекаем пробег
#                 mileage_match = re.search(r'(\d{1,3}(?: \d{3})*)\s*км', name_text)
#                 mileage = int(mileage_match.group(1).replace(" ", "")) if mileage_match else None
#
#                 # Извлекаем цену
#                 price_tag = item.select_one(".iva-item-priceStep-TIzu3")
#                 if price_tag:
#                     try:
#                         price_text = price_tag.get_text(strip=True).split("₽")[0]
#                         price_str = "".join(filter(str.isdigit, price_text))
#                         if price_str:
#                             price = int(price_str)
#
#                             # Учитываем пробег в проверке дубликатов
#                             # ad_id = f"{name_text}-{price}-{mileage if mileage else 'NA'}"
#                             # if ad_id in seen_ads:
#                             #     self.logger.debug(
#                             #         f"Страница {page}: Дубликат {name_text}, пробег: {mileage}, цена {price}, пропущено")
#                             #     continue
#                             # seen_ads.add(ad_id)
#
#                             if 100_000 <= price <= 200_000_000:
#                                 new_prices.append(price)
#                                 self.logger.debug(
#                                     f"Страница {page}: {name_text}, пробег: {mileage if mileage else 'не указан'}, цена {price} добавлена"
#                                 )
#                             else:
#                                 self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                     except ValueError:
#                         self.logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")
#
#             prices.extend(new_prices)
#             self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка кнопки "Следующая страница"
#             next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
#             if next_page:
#                 page += 1
#                 time.sleep(random.uniform(20, 35))  # Увеличена задержка
#             else:
#                 self.logger.info("Конец пагинации, завершаем парсинг.")
#                 break
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]


# import logging
# import re
# from bs4 import BeautifulSoup
# from utils import get_random_user_agent, safe_request, get_working_proxy
# import urllib.parse
# import time
# import random
# from datetime import datetime
#
# class AvitoParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year
#         self.base_url = "https://www.avito.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1
#
#         if isinstance(self.year, list):
#             if len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             elif len(self.year) == 2:
#                 start_year, end_year = self.year
#             else:
#                 self.logger.error("Неверный формат года. Укажите один год или диапазон через тире.")
#                 return prices
#         else:
#             start_year = end_year = 2000
#
#         while len(prices) < 100:
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/"
#                 f"{encoded_make}/{encoded_model}/"
#                 # f"?p={page}"
#                 f"?p={page}&radius=1000&searchRadius=1000"
#             )
#             headers = {
#                 "User-Agent": get_random_user_agent(),
#                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
#                 "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#                 "Upgrade-Insecure-Requests": "1",
#                 "Connection": "keep-alive",
#                 "Cache-Control": "max-age=0"
#             }
#             # proxy = get_working_proxy()  # Получаем прокси
#             # self.logger.info(f"Используется прокси: {proxy}") # Логируем прокси
#
#             response = safe_request(search_url, headers)  # `safe_request` уже подставляет прокси автоматически
#             if not response:
#                 self.logger.error(f"Не удалось получить страницу {page}")
#                 break
#
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#
#             # Извлекаем объявления
#             for item in soup.select(".iva-item-content-OWwoq"):
#                 name_tag = item.select_one('h3[itemprop="name"]')
#                 if not name_tag:
#                     self.logger.debug(f"Страница {page}: Объявление без имени")
#                     continue
#
#                 name_text = name_tag.get_text(strip=True).replace("\xa0", " ")  # Убираем неразрывные пробелы
#
#                 # Извлекаем год выпуска
#                 year_match = re.search(r'\b(\d{4})\b', name_text)
#                 if year_match:
#                     car_year = int(year_match.group(1))
#                     if car_year == start_year == end_year:
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, год {car_year}, добавлено"
#                         )
#                     elif start_year <= car_year <= end_year:
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, год {car_year}, добавлено"
#                         )
#                     else:
#                         self.logger.debug(
#                             f"Страница {page}: Объявление {name_text}, вне диапазона [{start_year}-{end_year}]"
#                         )
#                         continue
#                 else:
#                     self.logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
#                     continue
#
#                 # Извлекаем пробег
#                 mileage_match = re.search(r'(\d{1,3}(?: \d{3})*)\s*км', name_text)
#                 if mileage_match:
#                     mileage_text = mileage_match.group(1).replace(" ", "")  # Убираем пробелы в числе
#                     mileage = int(mileage_text)
#                 else:
#                     mileage = None  # Если пробег не найден, ставим None
#
#                 # Извлекаем цену
#                 price_tag = item.select_one(".iva-item-priceStep-TIzu3")
#                 if not price_tag:
#                     self.logger.debug(f"Страница {page}: {name_text}, без цены")
#                     continue
#
#                 price_meta = price_tag.select_one("meta[itemprop='price']")
#                 if price_meta:
#                     price = int(price_meta["content"])
#                     if 100_000 <= price <= 200_000_000:
#                         new_prices.append(price)
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, пробег: {mileage} км, цена {price} добавлена"
#                         )
#                     else:
#                         self.logger.debug(f"Страница {page}: Объявление {name_text}, цена {price} вне диапазона")
#                 else:
#                     try:
#                         price_text = price_tag.get_text(strip=True).split("₽")[0]
#                         price_str = "".join(filter(str.isdigit, price_text))
#                         if price_str:
#                             price = int(price_str)
#                             if 100_000 <= price <= 200_000_000:
#                                 new_prices.append(price)
#                                 self.logger.debug(
#                                     f"Страница {page}: {name_text}, пробег: {mileage} км, цена {price} добавлена"
#                                 )
#                             else:
#                                 self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                     except (ValueError, AttributeError):
#                         self.logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")
#
#             prices.extend(new_prices)
#             self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка кнопки "Следующая страница"
#             next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
#             if next_page:
#                 page += 1
#                 # time.sleep(random.uniform(10, 15))  # Умеренная задержка между запросами
#                 delay = random.uniform(15, 30)
#                 if random.random() < 0.2:  # 20% вероятности долгой задержки
#                     delay *= 2
#                 time.sleep(delay)
#
#             else:
#                 self.logger.info("Конец пагинации, завершаем парсинг.")
#                 break  # Останавливаем цикл, если страниц больше нет
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         # Пометка, если найдено менее 100 цен
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]
#
# # 84 год {car_year}, 111 {car_year}, 124 {car_year}, 105 {car_year},