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
    def __init__(self, make, model, year=None, stop_event=None, found_prices=None, lock=None, limit=100, use_proxy=True):
        self.make = make
        self.model = model
        self.year = year if isinstance(year, list) else [year] if year else []
        self.stop_event = stop_event  # Флаг остановки
        self.found_prices = found_prices  # Общий список цен
        self.lock = lock  # Блокировка для синхронизации
        self.limit = limit  # Сохраняем лимит
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
        page = 1

        # Определение диапазона годов
        if len(self.year) == 2:
            start_year, end_year = self.year
        elif len(self.year) == 1:
            start_year = end_year = self.year[0]
        else:
            start_year = end_year = None

        try:
            while not self.stop_event.is_set():
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
                    if self.stop_event.is_set():  # Проверяем флаг остановки перед каждым объявлением
                        break

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
                        item.select_one(".ListingItemPrice_highlighted .ListingItemPrice__content"),
                        # Выделенная цветом цена
                        item.select_one(".ListingItemPrice_withPopup .ListingItemPrice__content a span")
                        # Цена от X до X
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
                                    break
                                else:
                                    self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                            except ValueError:
                                self.logger.warning(f"Страница {page}: Ошибка парсинга цены для {name_text}")
                            break

                # Добавляем новые цены в общий список
                with self.lock:
                    self.found_prices.extend(new_prices)
                    self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен. Всего: {len(self.found_prices)}")
                    if len(self.found_prices) >= self.limit:  # Проверяем общий лимит
                        self.stop_event.set()  # Устанавливаем флаг остановки
                        self.logger.info(f"Достигнут лимит в {len(self.found_prices)} цен. Завершаю парсинг.")
                        return

                # Проверка пагинации
                next_page = soup.select_one(".ListingPagination__next")
                if not next_page or self.stop_event.is_set():
                    break

                page += 1
                delay = random.uniform(1, 3) if self.use_proxy else random.uniform(10, 15)
                self.logger.debug(f"Задержка перед следующей страницей: {delay:.2f} сек.")
                time.sleep(delay)

        except Exception as e:
            self.logger.error(f"Ошибка парсинга: {e}")
            raise
        finally:
            self.close_driver()  # Гарантированное закрытие WebDriver

        self.logger.info(f"Итог: {len(self.found_prices)} цен из {page} страниц")
