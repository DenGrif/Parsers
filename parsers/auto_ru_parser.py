# рабочий
import logging
import urllib.parse
import time
import random
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from utils import selenium_request


class SafeChrome(uc.Chrome):
    def __del__(self):
        try:
            if hasattr(self, 'service') and self.service.process:
                self.quit()
        except:
            pass


class AutoRuParser:
    def __init__(self, make, model, year=None, limit=100, use_proxy=True):
        self.make = make
        self.model = model
        self.year = year if isinstance(year, list) else [year] if year else []
        self.limit = limit
        self.use_proxy = use_proxy
        self.base_url = "https://auto.ru"
        self.logger = logging.getLogger(__name__)
        self.driver = None

        # Настройка ChromeOptions
        self.options = uc.ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-features=SecureDns")
        self.options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Создание WebDriver
        self.driver = SafeChrome(options=self.options)
        self.driver.get(self.base_url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()

    def close_driver(self):
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Ошибка при закрытии драйвера: {e}")
            finally:
                self.driver = None

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
            start_year = end_year = None

        try:
            while len(prices) < self.limit:
                search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
                html, self.driver, success = selenium_request(search_url, self.driver, use_proxy=self.use_proxy)

                if not success:
                    self.logger.error(f"Не удалось получить страницу {page}")
                    break

                # Парсим страницу
                soup = BeautifulSoup(html, "html.parser")
                new_prices = []
                self.logger.info(f"Обрабатываю страницу {page}...")

                # Извлекаем объявления
                for item in soup.select(".ListingItem"):
                    name_tag = item.select_one(".ListingItemTitle__link")
                    if not name_tag:
                        self.logger.debug(f"Страница {page}: Объявление без имени")
                        continue
                    name_text = name_tag.get_text(strip=True)

                    # Парсинг года
                    year_tag = item.select_one(".ListingItem__year")
                    if year_tag:
                        try:
                            car_year = int(year_tag.get_text(strip=True))
                            if start_year and end_year and not (start_year <= car_year <= end_year):
                                self.logger.debug(f"Страница {page}: Год {car_year} вне диапазона")
                                continue
                        except ValueError:
                            self.logger.debug(f"Страница {page}: Ошибка парсинга года")
                            continue

                    # Сохраняем все три варианта селекторов для цен
                    price_containers = [
                        item.select_one(".ListingItemPrice__content a span"),  # Обычная цена
                        item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),  # Выделенная цветом цена
                        item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span")
                        # Цена от X до X (берётся мин от Х цена)"
                    ]

                    for price_container in price_containers:
                        if price_container:
                            price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0",
                                                                                                       "").strip()
                            if price_text.startswith("от "):
                                price_text = price_text[3:]
                            try:
                                price = int(price_text)
                                if 100_000 <= price <= 200_000_000:
                                    new_prices.append(price)
                                    self.logger.debug(f"Страница {page}: {name_text}, Цена {price} добавлена")
                                    break  # Используем первое найденное значение
                                else:
                                    self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                            except ValueError:
                                self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
                            break  # Переходим к следующему объявлению после нахождения цены

                # Проверка, если достигли лимита
                if len(prices) + len(new_prices) >= self.limit:
                    self.logger.info(f"Достигнуто {self.limit} цен, завершаем парсинг.")
                    prices.extend(new_prices[:self.limit - len(prices)])
                    break

                prices.extend(new_prices)
                self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

                # Проверка пагинации
                next_page = soup.select_one(".ListingPagination__next")
                if not next_page:
                    break

                page += 1
                delay = random.uniform(1, 3) if self.use_proxy else random.uniform(10, 15)
                self.logger.debug(f"Задержка перед следующей страницей: {delay:.2f} сек.")
                time.sleep(delay)

        except Exception as e:
            self.logger.error(f"Ошибка парсинга: {e}")
            raise
        finally:
            self.close_driver() # Гарантированное закрытие WebDriver

        self.logger.info(f"Итог: {len(prices)} цен из {page} страниц")

        # Пометка, если найдено менее лимита цен
        if len(prices) < self.limit:
            self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
        return prices[:self.limit]


# попытка одного счётчика
# import logging
# import re
# import urllib.parse
# import time
# import random
# import undetected_chromedriver as uc
# from bs4 import BeautifulSoup
# from utils import selenium_request, setup_logging
#
# # Настройка логирования
# setup_logging()
# logger = logging.getLogger(__name__)
#
# class SafeChrome(uc.Chrome):
#     def __del__(self):
#         try:
#             if hasattr(self, 'service') and self.service.process:
#                 self.quit()
#         except:
#             pass
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None, use_proxy=True):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.use_proxy = use_proxy
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#         self.driver = None
#
#         # Настройка ChromeOptions
#         self.options = uc.ChromeOptions()
#         self.options.add_argument("--headless")
#         self.options.add_argument("--ignore-certificate-errors")
#         self.options.add_argument("--disable-blink-features=AutomationControlled")
#         self.options.add_argument("--disable-features=SecureDns")
#         self.options.add_argument(
#             "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         )
#
#         # Создание и запуск WebDriver
#         self.driver = SafeChrome(options=self.options)
#         self.driver.get(self.base_url)
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.close_driver()
#
#     def close_driver(self):
#         if hasattr(self, 'driver') and self.driver:
#             try:
#                 self.driver.quit()
#             except Exception as e:
#                 self.logger.warning(f"Ошибка при закрытии драйвера: {e}")
#             finally:
#                 self.driver = None
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
#             start_year = end_year = None
#
#         try:
#             while not stop_event.is_set():
#                 with collected_prices_lock:
#                     total_collected = collected_prices + len(prices)
#                     logger.debug(f"Проверка перед парсингом страницы {page}: collected_prices={collected_prices}, prices={len(prices)}, total_collected={total_collected}, limit={limit}")
#                     if total_collected >= limit:
#                         logger.info(f"Достигнуто общее количество цен: {limit}. Останавливаем парсинг.")
#                         stop_event.set()
#                         break
#
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html, self.driver, success = selenium_request(search_url, self.driver, use_proxy=self.use_proxy)
#
#                 if not success:
#                     self.logger.error(f"Не удалось получить страницу {page}")
#                     break
#
#                 # Парсим страницу
#                 soup = BeautifulSoup(html, "html.parser")
#                 new_prices = []
#                 self.logger.info(f"Обрабатываю страницу {page}...")
#
#                 # Извлекаем объявления
#                 for item in soup.select(".ListingItem"):
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         self.logger.debug(f"Страница {page}: Объявление без имени")
#                         continue
#                     name_text = name_tag.get_text(strip=True)
#
#                     # Парсинг года
#                     year_tag = item.select_one(".ListingItem__year")
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                             if start_year and end_year and not (start_year <= car_year <= end_year):
#                                 self.logger.debug(f"Страница {page}: Год {car_year} вне диапазона")
#                                 continue
#                         except ValueError:
#                             self.logger.debug(f"Страница {page}: Ошибка парсинга года")
#                             continue
#
#                     # Сохраняем все три варианта селекторов для цен
#                     price_containers = [
#                         item.select_one(".ListingItemPrice__content a span"),  # Обычная цена
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),  # Выделенная цветом цена
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span")
#                         # Цена от X до X (берётся мин от Х цена)"
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
#                                     break  # Используем первое найденное значение
#                                 else:
#                                     self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
#                             except ValueError:
#                                 self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
#                             break  # Переходим к следующему объявлению после нахождения цены
#
#                 prices.extend(new_prices)
#                 logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 # Проверка кнопки "Следующая страница"
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if next_page and "href" in next_page.attrs:
#                     page += 1
#                     delay = random.uniform(1, 3) if self.use_proxy else random.uniform(10, 15)
#                     self.logger.debug(f"Задержка перед следующей страницей: {delay:.2f} сек.")
#                     time.sleep(delay)
#                 else:
#                     logger.info("Конец пагинации, завершаем парсинг.")
#                     break
#
#         except Exception as e:
#             self.logger.error(f"Ошибка при парсинге: {e}")
#             raise
#         finally:
#             self.close_driver()  # Гарантированное закрытие WebDriver
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#
#         # Пометка, если найдено менее заданного лимита цен
#         if len(prices) < limit:
#             self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")
#         return prices



# import logging
# import urllib.parse
# import time
# import random
# import undetected_chromedriver as uc
# from bs4 import BeautifulSoup
# from utils import selenium_request
#
# class SafeChrome(uc.Chrome):
#     def __del__(self):
#         try:
#             if hasattr(self, 'service') and self.service.process:
#                 self.quit()
#         except:
#             pass
#
# class AutoRuParser:
#     def __init__(self, make, model, year=None, limit=100, use_proxy=True):
#         self.make = make
#         self.model = model
#         self.year = year if isinstance(year, list) else [year] if year else []
#         self.limit = limit
#         self.use_proxy = use_proxy
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#         self.driver = None
#         self._stop_parsing = False  # Флаг для остановки
#         self._force_stop = False    # Флаг для экстренной остановки
#
#         # Настройка ChromeOptions
#         self.options = uc.ChromeOptions()
#         self.options.add_argument("--headless")
#         self.options.add_argument("--ignore-certificate-errors")
#         self.options.add_argument("--disable-blink-features=AutomationControlled")
#         self.options.add_argument("--disable-features=SecureDns")
#         self.options.add_argument(
#             "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         )
#
#         # Создание WebDriver
#         self.driver = SafeChrome(options=self.options)
#         self.driver.get(self.base_url)
#
#     def stop(self):
#         """Экстренная остановка парсера"""
#         self._force_stop = True
#         self._stop_parsing = True
#         self.logger.info("Получена команда экстренной остановки")
#         self.close_driver()
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.close_driver()
#
#     def close_driver(self):
#         if hasattr(self, 'driver') and self.driver:
#             try:
#                 self.driver.quit()
#             except Exception as e:
#                 self.logger.warning(f"Ошибка при закрытии драйвера: {e}")
#             finally:
#                 self.driver = None
#
#     def parse(self):
#         if self._force_stop or self._stop_parsing:
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
#             start_year = end_year = None
#
#         try:
#             while len(prices) < self.limit and not self._stop_parsing:
#                 if self._force_stop:
#                     break
#
#                 search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/used/?page={page}"
#                 html, self.driver, success = selenium_request(search_url, self.driver, use_proxy=self.use_proxy)
#
#                 if not success or self._force_stop or self._stop_parsing:
#                     break
#
#                 # Парсим страницу
#                 soup = BeautifulSoup(html, "html.parser")
#                 new_prices = []
#                 self.logger.info(f"Обрабатываю страницу {page}...")
#
#                 # Извлекаем объявления
#                 for item in soup.select(".ListingItem"):
#                     if self._force_stop or self._stop_parsing:
#                         break
#
#                     name_tag = item.select_one(".ListingItemTitle__link")
#                     if not name_tag:
#                         continue
#
#                     name_text = name_tag.get_text(strip=True)
#
#                     # Парсинг года
#                     year_tag = item.select_one(".ListingItem__year")
#                     if year_tag:
#                         try:
#                             car_year = int(year_tag.get_text(strip=True))
#                             if start_year and end_year and not (start_year <= car_year <= end_year):
#                                 continue
#                         except ValueError:
#                             continue
#
#                     # Парсинг цены
#                     for price_container in [
#                         item.select_one(".ListingItemPrice__content a span"),
#                         item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
#                         item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span")
#                     ]:
#                         if price_container and not (self._force_stop or self._stop_parsing):
#                             try:
#                                 price_text = price_container.get_text(strip=True).replace("₽", "").replace("\xa0", "").strip()
#                                 if price_text.startswith("от "):
#                                     price_text = price_text[3:]
#                                 price = int(price_text)
#                                 if 100_000 <= price <= 200_000_000:
#                                     new_prices.append(price)
#                                     break
#                             except ValueError:
#                                 continue
#
#                     # Проверка лимита после каждого объявления
#                     if len(prices) + len(new_prices) >= self.limit:
#                         prices.extend(new_prices[:self.limit - len(prices)])
#                         self.logger.info(f"Достигнут лимит {self.limit} цен")
#                         return prices[:self.limit]
#
#                 prices.extend(new_prices)
#                 self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#                 # Проверка пагинации
#                 next_page = soup.select_one(".ListingPagination__next")
#                 if not next_page or self._force_stop or self._stop_parsing:
#                     break
#
#                 page += 1
#                 delay = random.uniform(1, 3) if self.use_proxy else random.uniform(10, 15)
#                 end_time = time.time() + delay
#                 while time.time() < end_time and not (self._force_stop or self._stop_parsing):
#                     time.sleep(0.1)
#
#         except Exception as e:
#             if not self._force_stop:
#                 self.logger.error(f"Ошибка парсинга: {e}")
#             raise
#         finally:
#             self.close_driver()
#
#         self.logger.info(f"Завершено. Обработано {page} страниц, собрано {len(prices)} цен")
#         return prices[:self.limit]


