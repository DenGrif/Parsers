import logging
from bs4 import BeautifulSoup
import urllib.parse
from utils import get_random_user_agent, get_random_proxy, safe_request

# вариант с debag
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

# **************************************************************************
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
#         prices = []
#         page = 1
#         max_pages = 5  # Максимум 5 страниц
#
#         while len(prices) < 100 and page <= max_pages:
#             search_url = (
#                 f"{self.base_url}/moskva/cars/{encoded_make}/{encoded_model}/all/"
#                 f"?page={page}"
#             )
#             headers = {
#                 "User-Agent": get_random_user_agent(),
#                 "Referer": "https://auto.ru/moskva/cars/all/",
#                 "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#             }
#             proxy = get_random_proxy()
#
#             response = safe_request(search_url, headers=headers, proxy=proxy)
#             if not response:
#                 self.logger.error(f"Не удалось получить страницу {page}")
#                 break
#
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#
#             # Используем meta-теги для цены
#             for item in soup.select("meta[itemprop='price']"):
#                 try:
#                     price = int(item["content"])
#                     if 100_000 <= price <= 200_000_000:
#                         new_prices.append(price)
#                 except (ValueError, KeyError):
#                     self.logger.warning("Ошибка парсинга цены через meta-теги")
#
#             # Резервный парсинг через CSS-селектор
#             if not new_prices:
#                 for price_container in soup.select(".ListingItemPrice__content span"):
#                     try:
#                         price_text = price_container.get_text(strip=True).replace("₽", "").replace(" ", "")
#                         price = int("".join(filter(str.isdigit, price_text)))
#                         if 100_000 <= price <= 200_000_000:
#                             new_prices.append(price)
#                     except (ValueError, AttributeError):
#                         self.logger.warning("Ошибка парсинга цены через CSS-селектор")
#
#             prices.extend(new_prices)
#             self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             # Проверка на наличие следующей страницы
#             next_page_link = soup.select_one("a[aria-label='Следующая страница']")
#             if not next_page_link:
#                 break
#
#             page += 1
#             time.sleep(2)  # Задержка между запросами
#
#         self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
#         return prices[:100]

#**************************************************************************************
# вариант с debag:
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
#         # Выводим HTML для отладки (если цены не парсятся)
#         with open("debug.html", "w", encoding="utf-8") as f:
#             f.write(response.text)
#
#         # Используем селектор для цены
#         for price_container in soup.select(".ListingItemPrice__content"):
#             price_span = price_container.select_one("span")
#             if price_span:
#                 try:
#                     price_text = price_span.get_text(strip=True)
#                     price_text = price_text.replace("₽", "").replace(" ", "")
#                     price = int("".join(filter(str.isdigit, price_text)))
#                     if 100_000 <= price <= 200_000_000:
#                         prices.append(price)
#                 except (ValueError, AttributeError):
#                     self.logger.warning("Ошибка парсинга цены на Auto.ru")
#             else:
#                 self.logger.warning("Не найден элемент с ценой в контейнере")
#
#         self.logger.info(f"Получено {len(prices)} цен с Auto.ru")
#         return prices[:100]
# *************************************************************************************
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