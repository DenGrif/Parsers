import logging
from bs4 import BeautifulSoup
from utils import get_random_user_agent, get_random_proxy, safe_request
import urllib.parse
import time


class AvitoParser:
    def __init__(self, make, model):
        self.make = make
        self.model = model
        self.base_url = "https://www.avito.ru"
        self.logger = logging.getLogger(__name__)

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        prices = []
        page = 1

        while len(prices) < 100 and page <= 10:
            search_url = (
                f"{self.base_url}/moskva/avtomobili/"
                f"{encoded_make}/{encoded_model}/"
                f"?p={page}&radius=1000&searchRadius=1000"
            )
            headers = {"User-Agent": get_random_user_agent()}
            proxy = get_random_proxy()

            response = safe_request(search_url, headers, proxy)
            if not response:
                self.logger.error(f"Не удалось получить страницу {page}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            new_prices = []

            # Извлекаем цены через meta-теги
            for item in soup.select(".iva-item-priceStep-TIzu3"):
                price_meta = item.select_one("meta[itemprop='price']")
                if price_meta:
                    price = int(price_meta["content"])
                    if 100_000 <= price <= 200_000_000:
                        new_prices.append(price)
                else:
                    try:
                        price_text = item.get_text(strip=True).split("₽")[0]
                        price_str = "".join(filter(str.isdigit, price_text))
                        if price_str:
                            price = int(price_str)
                            if 100_000 <= price <= 200_000_000:
                                new_prices.append(price)
                    except (ValueError, AttributeError):
                        self.logger.warning("Ошибка парсинга цены")

            prices.extend(new_prices)
            self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

            page += 1
            time.sleep(2)  # Задержка между запросами

        self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
        return prices[:100]
