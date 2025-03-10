import logging
from bs4 import BeautifulSoup
import urllib.parse
from utils import get_random_user_agent, get_random_proxy, safe_request


class AutoRuParser:
    def __init__(self, make, model):
        self.make = make
        self.model = model
        self.base_url = "https://auto.ru"
        self.logger = logging.getLogger(__name__)

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        search_url = (
            f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/all/"
        )
        headers = {"User-Agent": get_random_user_agent()}
        proxy = get_random_proxy()

        response = safe_request(search_url, headers, proxy)
        if not response:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        prices = []

        # Выводим HTML для отладки (если цены не парсятся)
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Используем селектор для цены
        for price_container in soup.select(".ListingItemPrice__content"):
            price_span = price_container.select_one("span")
            if price_span:
                try:
                    price_text = price_span.get_text(strip=True)
                    price_text = price_text.replace("₽", "").replace(" ", "")
                    price = int("".join(filter(str.isdigit, price_text)))
                    if 100_000 <= price <= 200_000_000:
                        prices.append(price)
                except (ValueError, AttributeError):
                    self.logger.warning("Ошибка парсинга цены на Auto.ru")
            else:
                self.logger.warning("Не найден элемент с ценой в контейнере")

        self.logger.info(f"Получено {len(prices)} цен с Auto.ru")
        return prices[:100]

# import logging
# from bs4 import BeautifulSoup
# import urllib.parse
# from utils import get_random_user_agent, get_random_proxy, safe_request
#
#
# class AutoRuParser:
#     def __init__(self, make, model):
#         self.make = make
#         self.model = model
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         search_url = (
#             f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/all/"
#         )
#         headers = {"User-Agent": get_random_user_agent()}
#         proxy = get_random_proxy()
#
#         response = safe_request(search_url, headers, proxy)
#         if not response:
#             return []
#
#         soup = BeautifulSoup(response.text, "html.parser")
#         prices = []
#
#         # Используем правильный селектор для цены
#         for item in soup.select("ListingItemPrice__content span"):
#             try:
#                 price_text = item.get_text(strip=True).replace("₽", "").replace(" ", "")
#                 price = int("".join(filter(str.isdigit, price_text)))
#                 if 100_000 <= price <= 200_000_000:
#                     prices.append(price)
#             except (ValueError, AttributeError):
#                 self.logger.warning("Ошибка парсинга цены на Auto.ru")
#
#         self.logger.info(f"Получено {len(prices)} цен с Auto.ru")
#         return prices[:100]
#*************************************************************************************8
# import logging
# from bs4 import BeautifulSoup
# import urllib.parse
# from utils import get_random_user_agent, get_random_proxy, safe_request
#
#
# class AutoRuParser:
#     def __init__(self, make, model):
#         self.make = make
#         self.model = model
#         self.base_url = "https://auto.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         search_url = f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/all/"
#         headers = {"User-Agent": get_random_user_agent()}
#         proxy = get_random_proxy()
#
#         response = safe_request(search_url, headers, proxy)
#         if not response:
#             return []
#
#         soup = BeautifulSoup(response.text, "html.parser")
#         prices = []
#         # Селекторы могут устареть — проверьте через инструменты разработчика!
#         for item in soup.select(".ListingItemPrice__content"):
#             try:
#                 price_text = item.get_text(strip=True).replace("₽", "").replace(" ", "")
#                 price = int(price_text)
#                 prices.append(price)
#             except (ValueError, AttributeError):
#                 self.logger.warning("Ошибка парсинга цены на Auto.ru")
#
#         self.logger.info(f"Получено {len(prices)} цен с Auto.ru")
#         return prices[:100]