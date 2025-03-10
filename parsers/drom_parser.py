import logging
from bs4 import BeautifulSoup
from utils import get_random_user_agent, get_random_proxy, safe_request
import urllib.parse
import time


class DromParser:
    def __init__(self, make, model):
        self.make = make
        self.model = model
        self.base_url = "https://auto.drom.ru"
        self.logger = logging.getLogger(__name__)

    def parse(self):
        encoded_make = urllib.parse.quote(self.make.lower())
        encoded_model = urllib.parse.quote(self.model.lower())
        prices = []
        page = 1
        max_pages = 10  # Максимум 10 страниц

        while len(prices) < 100 and page <= max_pages:
            search_url = f"{self.base_url}/{encoded_make}/{encoded_model}/page{page}/"
            headers = {"User-Agent": get_random_user_agent()}
            proxy = get_random_proxy()

            response = safe_request(search_url, headers, proxy)
            if not response:
                self.logger.error(f"Не удалось получить страницу {page}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            new_prices = []

            # Извлекаем цены через data-ftid
            for item in soup.select("[data-ftid='bull_price']"):
                try:
                    price_text = item.get_text(strip=True).replace("₽", "").replace(" ", "")
                    price = int("".join(filter(str.isdigit, price_text)))
                    if 100_000 <= price <= 200_000_000:
                        new_prices.append(price)
                except (ValueError, AttributeError):
                    self.logger.warning("Ошибка парсинга цены на Drom.ru")

            prices.extend(new_prices)
            self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")

            # Проверяем, есть ли следующая страница
            next_page_link = soup.select_one("a[data-ftid='component_pagination-item-next']")
            if not next_page_link:
                break

            page += 1
            time.sleep(2)  # Задержка между запросами

        self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
        return prices[:100]
#***************************************************************************************
# import logging
# import time
# from bs4 import BeautifulSoup
# import urllib.parse
# from utils import get_random_user_agent, get_random_proxy, safe_request
#
# class DromParser:
#     def __init__(self, make, model):
#         self.make = make
#         self.model = model
#         self.base_url = "https://auto.drom.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1
#
#         while len(prices) < 100 and page <= 5:
#             search_url = (
#                 f"{self.base_url}/{encoded_make}/{encoded_model}/"
#                 f"?page={page}"
#             )
#             headers = {"User-Agent": get_random_user_agent()}
#             proxy = get_random_proxy()
#
#             response = safe_request(search_url, headers, proxy)
#             if not response:
#                 self.logger.error(f"Не удалось получить страницу {page}")
#                 break
#
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#
#             for item in soup.select("[data-ftid='bull_price']"):
#                 try:
#                     price_text = item.get_text(strip=True).replace("₽", "").replace(" ", "")
#                     price = int("".join(filter(str.isdigit, price_text)))
#                     if 100_000 <= price <= 200_000_000:
#                         new_prices.append(price)
#                 except (ValueError, AttributeError):
#                     self.logger.warning("Ошибка парсинга цены на Drom.ru")
#
#             prices.extend(new_prices)
#             self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка наличия следующей страницы
#             next_page_link = soup.select_one(".next-page")
#             if not next_page_link:
#                 break
#
#             page += 1
#             time.sleep(2)
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#         return prices[:100]

# *********************************************************************************
# import logging
# from bs4 import BeautifulSoup
# import urllib.parse
# from utils import get_random_user_agent, get_random_proxy, safe_request
#
#
# class DromParser:
#     def __init__(self, make, model):
#         self.make = make
#         self.model = model
#         self.base_url = "https://www.drom.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         search_url = f"{self.base_url}/{encoded_make}/{encoded_model}"
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
#         for item in soup.select(".bull_price"):
#             try:
#                 price_text = item.get_text(strip=True).replace("₽", "").replace(" ", "")
#                 price = int(price_text)
#                 prices.append(price)
#             except (ValueError, AttributeError):
#                 self.logger.info("Ошибка парсинга цены на auto.drom.ru")
#                 self.logger.warning("Ошибка парсинга цены на auto.drom.ru")
#
#         self.logger.info(f"Получено {len(prices)} цен с Drom.ru")
#         return prices[:100]