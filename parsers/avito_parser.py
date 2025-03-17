import logging
from bs4 import BeautifulSoup
from utils import get_random_user_agent, get_random_proxy, safe_request
import urllib.parse
import time
import re
import random
from datetime import datetime


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

        start_year = self.year if self.year else 2000
        end_year = datetime.now().year

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
            proxy = get_random_proxy()

            response = safe_request(search_url, headers, proxy)
            if not response:
                self.logger.error(f"Не удалось получить страницу {page}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            new_prices = []

            # Извлекаем цены и проверяем год выпуска
            for item in soup.select(".iva-item-content-OWwoq"):
                name_tag = item.select_one('h3[itemprop="name"]')
                if not name_tag:
                    self.logger.debug(f"Страница {page}: Объявление без имени")
                    continue

                name_text = name_tag.get_text(strip=True)
                match = re.search(r'\b(\d{4})\b', name_text)
                if match:
                    car_year = int(match.group(1))
                    if not (start_year <= car_year <= end_year):
                        self.logger.debug(
                            f"Страница {page}: Объявление {name_text}, год {car_year} не в диапазоне [{start_year}-{end_year}]"
                        )
                        continue
                else:
                    self.logger.debug(f"Страница {page}: Объявление {name_text} без года выпуска")
                    continue

                price_tag = item.select_one(".iva-item-priceStep-TIzu3")
                if not price_tag:
                    self.logger.debug(f"Страница {page}: Объявление {name_text} без цены")
                    continue

                price_meta = price_tag.select_one("meta[itemprop='price']")
                if price_meta:
                    price = int(price_meta["content"])
                    if 100_000 <= price <= 200_000_000:
                        new_prices.append(price)
                        self.logger.debug(f"Страница {page}: {name_text}, {car_year}, цена {price} добавлена")
                    else:
                        self.logger.debug(f"Страница {page}: Объявление {name_text}, цена {price} вне диапазона")
                else:
                    try:
                        price_text = price_tag.get_text(strip=True).split("₽")[0]
                        price_str = "".join(filter(str.isdigit, price_text))
                        if price_str:
                            price = int(price_str)
                            if 100_000 <= price <= 200_000_000:
                                new_prices.append(price)
                                self.logger.debug(f"Страница {page}: {name_text}, {car_year}, цена {price} добавлена")
                            else:
                                self.logger.debug(f"Страница {page}: Цена {price} вне диапазона")
                    except (ValueError, AttributeError):
                        self.logger.warning(f"Страница {page}: Ошибка парсинга цены для объявления {name_text}")

            prices.extend(new_prices)
            self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

            # 🔹 **Проверка наличия кнопки "Следующая страница"**
            next_page = soup.select_one('[data-marker="pagination-button/nextPage"]')
            if next_page:
                page += 1
                time.sleep(random.uniform(10, 15))  # Увеличенная задержка между запросами
            else:
                self.logger.info("Конец пагинации, завершаем парсинг.")
                break  # 🔹 Останавливаем цикл, если страниц больше нет

        self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")

        # Пометка, если найдено менее 100 цен
        if len(prices) < 100:
            self.logger.warning(f"Найдено всего {len(prices)} цен, расчет производится на основе имеющихся данных.")

        return prices[:100]
