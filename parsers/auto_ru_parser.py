import logging
import urllib.parse
import time
import random
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

            if isinstance(self.year, list) and len(self.year) == 2:
                start_year, end_year = self.year
            elif isinstance(self.year, list) and len(self.year) == 1:
                start_year = end_year = self.year[0]
            else:
                start_year = end_year = None

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

                    # Парсинг цен
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
                                    self.logger.debug(f"Страница {page}: {name_text}, Год {car_year}, Цена {price} добавлена")
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
                    time.sleep(random.uniform(10, 15))  # Задержка для маскировки
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


# import logging
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from utils import selenium_request
#
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()), options=options
#         )
#
#         try:
#             encoded_make = urllib.parse.quote(self.make.lower())
#             encoded_model = urllib.parse.quote(self.model.lower())
#             prices = []
#             page = 1
#
#             if isinstance(self.year, list) and len(self.year) == 2:
#                 start_year, end_year = self.year
#             elif isinstance(self.year, list) and len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             else:
#                 start_year = end_year = None
#
#             while len(prices) < 100:
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html = selenium_request(search_url, driver)
#                 soup = BeautifulSoup(html, "html.parser")
#
#                 new_prices = []
#                 for item in soup.select(".ListingItem"):
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         self.logger.debug(f"Страница {page}: Объявление без имени")
#                         continue
#
#                     name_text = name_tag.get_text(strip=True)
#
#                     # Парсинг года (инициализация перед использованием!)
#                     car_year = None
#                     year_tag = item.select_one(".ListingItem__yearBlock .ListingItem__year")
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                             if start_year and end_year and not (start_year <= car_year <= end_year):
#                                 self.logger.debug(f"Страница {page}: {name_text}, Год {car_year} вне диапазона")
#                                 continue
#                         except ValueError:
#                             self.logger.debug(f"Страница {page}: Ошибка парсинга года в {name_text}")
#                             continue
#
#                     # Парсинг цен
#                     price = None
#                     price_containers = [
#                         item.select_one(".ListingItemPrice__content a span"),
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span"),
#                     ]
#
#                     for price_container in price_containers:
#                         if price_container:
#                             price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
#                             if price_text.startswith("от "):
#                                 price_text = price_text[3:]
#                             try:
#                                 price = int(price_text)
#                                 if 100_000 <= price <= 200_000_000:
#                                     new_prices.append(price)
#                                     self.logger.debug(f"Страница {page}: {name_text}, Год {car_year}, Цена {price} добавлена")
#                                 else:
#                                     self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                             except ValueError:
#                                 self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
#                             break  # Выход после успешного нахождения цены
#
#                 prices.extend(new_prices)
#                 self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 if len(prices) >= 100:
#                     self.logger.info("Достигнуто 100 цен, завершаем парсинг.")
#                     break
#
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if next_page and "href" in next_page.attrs:
#                     page += 1
#                     time.sleep(random.uniform(10, 15))  # Задержка для маскировки
#                 else:
#                     self.logger.info("Конец пагинации, завершаем парсинг.")
#                     break
#         finally:
#             driver.quit()
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]



# import logging
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from utils import selenium_request
#
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#         self.seen_ads = set()  # Храним уникальные объявления (название, год, цена)
#
#     def parse(self):
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()), options=options
#         )
#
#         try:
#             encoded_make = urllib.parse.quote(self.make.lower())
#             encoded_model = urllib.parse.quote(self.model.lower())
#             prices = []
#             page = 1
#
#             if isinstance(self.year, list) and len(self.year) == 2:
#                 start_year, end_year = self.year
#             elif isinstance(self.year, list) and len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             else:
#                 start_year = end_year = None
#
#             while len(prices) < 100:
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html = selenium_request(search_url, driver)
#                 soup = BeautifulSoup(html, "html.parser")
#
#                 # Извлечение цен
#                 new_prices = []
#                 for item in soup.select(".ListingItem"):
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         self.logger.debug(f"Страница {page}: Объявление без имени")
#                         continue
#
#                     name_text = name_tag.get_text(strip=True)
#
#                     # Парсинг цен (ПЕРЕНЕСЕНО ВПЕРЁД!)
#                     price = None
#                     price_containers = [
#                         item.select_one(".ListingItemPrice__content a span"),
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span"),
#                     ]
#
#                     for price_container in price_containers:
#                         if price_container:
#                             price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
#                             if price_text.startswith("от "):
#                                 price_text = price_text[3:]
#                             try:
#                                 price = int(price_text)
#                                 break  # Выход после успешного нахождения цены
#                             except ValueError:
#                                 self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
#                                 continue
#
#                     if not price or not (100_000 <= price <= 200_000_000):
#                         self.logger.debug(f"Страница {page}: {name_text}, Цена {price if price else 'не указана'}, вне диапазона")
#                         continue
#
#                     # Парсинг года (теперь проверяется ПОСЛЕ цены)
#                     year_tag = item.select_one(".ListingItem__yearBlock .ListingItem__year")
#                     car_year = None
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                         except ValueError:
#                             self.logger.debug(f"Страница {page}: Ошибка парсинга года в {name_text}")
#                             continue
#
#                     if car_year and start_year and end_year and not (start_year <= car_year <= end_year):
#                         self.logger.debug(f"Страница {page}: {name_text}, Год {car_year}, Цена {price}, вне диапазона")
#                         continue
#
#                     # Проверка на дубликаты
#                     ad_key = (name_text, car_year, price)
#                     if ad_key in self.seen_ads:
#                         self.logger.debug(f"Страница {page}: Дубликат {name_text}, Год {car_year}, Цена {price}, пропущено")
#                         continue
#
#                     self.seen_ads.add(ad_key)  # Добавляем в список уникальных
#                     new_prices.append(price)
#                     self.logger.debug(f"Страница {page}: {name_text}, Год {car_year}, Цена {price} добавлена")
#
#                 prices.extend(new_prices)
#                 self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 if len(prices) >= 100:
#                     self.logger.info("Достигнуто 100 цен, завершаем парсинг.")
#                     break
#
#                 # Проверка пагинации
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if next_page and "href" in next_page.attrs:
#                     page += 1
#                     time.sleep(random.uniform(10, 15))  # Задержка для маскировки
#                 else:
#                     self.logger.info("Конец пагинации, завершаем парсинг.")
#                     break
#         finally:
#             driver.quit()  # Гарантированное закрытие WebDriver
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]


# был рабочий пока не поменял местами год вниз, по цене наверх/ стал работать, но опять цена none временами
# import logging
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from utils import selenium_request
#
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()), options=options
#         )
#
#         try:
#             encoded_make = urllib.parse.quote(self.make.lower())
#             encoded_model = urllib.parse.quote(self.model.lower())
#             prices = []
#             page = 1
#
#             if isinstance(self.year, list) and len(self.year) == 2:
#                 start_year, end_year = self.year
#             elif isinstance(self.year, list) and len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             else:
#                 start_year = end_year = None
#
#             while len(prices) < 100:  # Без ограничения на страницы
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html = selenium_request(search_url, driver)
#                 soup = BeautifulSoup(html, "html.parser")
#
#                 # Извлечение цен
#                 new_prices = []
#                 for item in soup.select(".ListingItem"):
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         self.logger.debug(f"Страница {page}: Объявление без имени")
#                         continue
#
#                     name_text = name_tag.get_text(strip=True)
#
#
#
#                     # Парсинг цен
#                     price = None
#                     price_containers = [
#                         item.select_one(".ListingItemPrice__content a span"),
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span"),
#                     ]
#
#                     for price_container in price_containers:
#                         if price_container:
#                             price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
#                             if price_text.startswith("от "):
#                                 price_text = price_text[3:]
#                             try:
#                                 price = int(price_text)
#                                 if 100_000 <= price <= 200_000_000:
#                                     new_prices.append(price)
#                                     self.logger.debug(f"Страница {page}: {name_text}, Цена {price} добавлена")
#                                 else:
#                                     self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                             except ValueError:
#                                 self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
#                             break  # Выход после успешного нахождения цены
#
#                     # Парсинг года
#                     year_tag = item.select_one(".ListingItem__yearBlock .ListingItem__year")
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                             if not (start_year <= car_year <= end_year):
#                                 self.logger.debug(f"Страница {page}: {name_text}, Цена {price}, Год {car_year} вне диапазона")
#                                 continue
#                         except ValueError:
#                             self.logger.debug(f"Страница {page}: Ошибка парсинга года")
#                             continue
#
#                 prices.extend(new_prices)
#                 self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 # Проверка, если достигли 100 цен
#                 if len(prices) >= 100:
#                     self.logger.info("Достигнуто 100 цен, завершаем парсинг.")
#                     break
#
#                 # Проверка пагинации
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if next_page and "href" in next_page.attrs:
#                     page += 1
#                     time.sleep(random.uniform(10, 15))  # Задержка для маскировки
#                 else:
#                     self.logger.info("Конец пагинации, завершаем парсинг.")
#                     break
#         finally:
#             driver.quit()  # Гарантированное закрытие WebDriver
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         # Пометка, если найдено менее 100 цен
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]


# import logging
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from utils import selenium_request
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()), options=options
#         )
#
#         try:
#             encoded_make = urllib.parse.quote(self.make.lower())
#             encoded_model = urllib.parse.quote(self.model.lower())
#             prices = []
#             seen_ads = set()  # Проверка дубликатов
#             page = 1
#
#             # Определяем диапазон поиска по году
#             if len(self.year) == 2:
#                 start_year, end_year = self.year
#             elif len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             else:
#                 start_year = end_year = None
#
#             while len(prices) < 100:
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html = selenium_request(search_url, driver)
#                 soup = BeautifulSoup(html, "html.parser")
#
#                 new_prices = []
#                 for item in soup.select(".ListingItem"):
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         self.logger.debug(f"Страница {page}: Объявление без имени")
#                         continue
#
#                     name_text = name_tag.get_text(strip=True)
#                     car_year = None
#                     price = None
#
#                     # Парсинг года
#                     year_tag = item.select_one(".ListingItem__yearBlock .ListingItem__year")
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                         except ValueError:
#                             self.logger.debug(f"Страница {page}: {name_text}, Ошибка парсинга года")
#                             continue
#
#                     # Парсинг цены
#                     price_containers = [
#                         item.select_one(".ListingItemPrice__content a span"),
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span"),
#                     ]
#
#                     for price_container in price_containers:
#                         if price_container:
#                             price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
#                             if price_text.startswith("от "):
#                                 price_text = price_text[3:]
#                             try:
#                                 price = int(price_text)
#                                 break
#                             except ValueError:
#                                 self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
#                                 continue
#
#                     # Проверка соответствия года диапазону
#                     if car_year and start_year and end_year and not (start_year <= car_year <= end_year):
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, Год {car_year}, Цена: {price if price else 'не указана'}, вне диапазона"
#                         )
#                         continue
#
#                     # Учитываем дубликаты (по названию и цене)
#                     ad_id = f"{name_text}-{price}"
#                     if ad_id in seen_ads:
#                         self.logger.debug(f"Страница {page}: Дубликат {name_text}, Цена: {price}, пропущено")
#                         continue
#                     seen_ads.add(ad_id)
#
#                     if price and 100_000 <= price <= 200_000_000:
#                         new_prices.append(price)
#                         self.logger.debug(f"Страница {page}: {name_text}, {car_year}, Цена: {price}, добавлена")
#                     else:
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, {car_year}, Цена: {price if price else 'не указана'}, вне диапазона"
#                         )
#
#                 prices.extend(new_prices)
#                 self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 if len(prices) >= 100:
#                     self.logger.info("Достигнуто 100 цен, завершаем парсинг.")
#                     break
#
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if next_page and "href" in next_page.attrs:
#                     page += 1
#                     time.sleep(random.uniform(10, 15))
#                 else:
#                     self.logger.info("Конец пагинации, завершаем парсинг.")
#                     break
#         finally:
#             driver.quit()
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]

# ***************************************************************************************

# import logging
# import urllib.parse
# import time
# import random
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from utils import selenium_request
#
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(
#             service=Service(ChromeDriverManager().install()), options=options
#         )
#
#         try:
#             encoded_make = urllib.parse.quote(self.make.lower())
#             encoded_model = urllib.parse.quote(self.model.lower())
#             prices = []
#             page = 1
#
#             # Определяем диапазон поиска по году
#             if len(self.year) == 2:
#                 start_year, end_year = self.year
#             elif len(self.year) == 1:
#                 start_year = end_year = self.year[0]
#             else:
#                 start_year = end_year = None  # Если год не указан, не фильтруем по году
#
#             while len(prices) < 100:
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html = selenium_request(search_url, driver)
#                 soup = BeautifulSoup(html, "html.parser")
#
#                 new_prices = []
#                 for item in soup.select(".ListingItem"):
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         self.logger.debug(f"Страница {page}: Объявление без имени")
#                         continue
#
#                     name_text = name_tag.get_text(strip=True)
#                     car_year = None
#                     price = None
#
#                     # Парсинг года
#                     year_tag = item.select_one(".ListingItem__yearBlock .ListingItem__year")
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                         except ValueError:
#                             self.logger.debug(f"Страница {page}: {name_text}, Ошибка парсинга года")
#                             continue
#
#                     # Парсинг цен
#                     price_containers = [
#                         item.select_one(".ListingItemPrice__content a span"),
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span"),
#                     ]
#
#                     for price_container in price_containers:
#                         if price_container:
#                             price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0",
#                                                                                                        "").strip()
#                             if price_text.startswith("от "):
#                                 price_text = price_text[3:]  # Берем минимальную цену
#                             try:
#                                 price = int(price_text)
#                                 break  # Выход после успешного нахождения цены
#                             except ValueError:
#                                 self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
#                                 continue
#
#                     # Проверка соответствия года диапазону
#                     if car_year and start_year and end_year and not (start_year <= car_year <= end_year):
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, Год {car_year}, Цена: {price if price else 'не указана'}, вне диапазона")
#                         continue
#
#                     if price and 100_000 <= price <= 200_000_000:
#                         new_prices.append(price)
#                         self.logger.debug(f"Страница {page}: {name_text}, {car_year}, Цена: {price}, добавлена")
#                     else:
#                         self.logger.debug(
#                             f"Страница {page}: {name_text}, {car_year}, Цена: {price if price else 'не указана'}, вне диапазона")
#
#                 prices.extend(new_prices)
#                 self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 if len(prices) >= 100:
#                     self.logger.info("Достигнуто 100 цен, завершаем парсинг.")
#                     break
#
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if next_page and "href" in next_page.attrs:
#                     page += 1
#                     time.sleep(random.uniform(10, 15))
#                 else:
#                     self.logger.info("Конец пагинации, завершаем парсинг.")
#                     break
#         finally:
#             driver.quit()
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         if len(prices) < 100:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#
#         return prices[:100]


