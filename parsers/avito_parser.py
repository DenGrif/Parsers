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

            # Проверка на наличие кнопки "Следующая страница"
            next_page_link = soup.select_one("a[data-marker='pagination-button/nextPage']")
            if not next_page_link:
                break

            page += 1
            time.sleep(2)  # Задержка между запросами

        self.logger.info(f"Обработано {page} страниц, получено {len(prices)} цен")
        return prices[:100]

# **************************************************

# import logging
# import time
# from bs4 import BeautifulSoup
# from utils import get_random_user_agent, get_random_proxy, safe_request
# import urllib.parse
#
#
# class AvitoParser:
#     def __init__(self, make, model):
#         self.make = make
#         self.model = model
#         self.base_url = "https://www.avito.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         prices = []
#         page = 1  # Начинаем с 1-й страницы
#
#         while len(prices) < 100:  # Собираем пока не накопится 100 цен или не закончатся страницы
#             search_url = (
#                 f"{self.base_url}/moskva/avtomobili/"
#                 f"{encoded_make}/{encoded_model}/"
#                 f"?cd={page}&radius=200&searchRadius=200"
#             )
#             headers = {"User-Agent": get_random_user_agent()}
#             proxy = get_random_proxy()
#
#             response = safe_request(search_url, headers, proxy)
#             if not response:
#                 break  # Если запрос не удался — выходим
#
#             soup = BeautifulSoup(response.text, "html.parser")
#             new_prices = []
#
#             # Извлекаем цены с текущей страницы
#             for item in soup.select(".iva-item-priceStep-TIzu3 span"):
#                 try:
#                     price_text = item.get_text(strip=True).replace("₽", "").replace(" ", "")
#                     price = int("".join(filter(str.isdigit, price_text)))
#                     new_prices.append(price)
#                 except (ValueError, AttributeError):
#                     self.logger.warning("Ошибка парсинга цены на Avito")
#
#             if not new_prices:  # Если страница пуста — выходим
#                 break
#
#             prices.extend(new_prices)
#             self.logger.info(f"Страница {page}: добавлено {len(new_prices)} цен")
#
#             page += 1  # Переходим на следующую страницу
#             time.sleep(2)  # Задержка между запросами
#
#             # Ограничение на количество страниц (избегаем бесконечного цикла)
#             if page > 10:
#                 break
#
#         self.logger.info(f"Обработано {page - 1} страниц, получено {len(prices)} цен")
#         return prices[:100]  # Оставляем максимум 100 цен

# # ********************************************************************
# import logging
# from bs4 import BeautifulSoup
# from utils import get_random_user_agent, get_random_proxy, safe_request
# import urllib.parse
#
#
# class AvitoParser:
#     def __init__(self, make, model):
#         self.make = make
#         self.model = model
#         self.base_url = "https://www.avito.ru"
#         self.logger = logging.getLogger(__name__)
#
#     def parse(self):
#         encoded_make = urllib.parse.quote(self.make.lower())
#         encoded_model = urllib.parse.quote(self.model.lower())
#         search_url = (
#             f"{self.base_url}/moskva/avtomobili/"
#             f"{encoded_make}/{encoded_model}/"
#             "?cd=1&radius=200&searchRadius=200"
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
#         for price_container in soup.select(".iva-item-priceStep-TIzu3"):
#             try:
#                 # Первым делом проверяем meta-тег
#                 price_meta = price_container.select_one("meta[itemprop='price']")
#                 if price_meta:
#                     price = int(price_meta["content"])
#                     prices.append(price)
#                 else:
#                     # Если meta-тега нет, извлекаем цену из текста
#                     price_text = price_container.get_text(strip=True).split("₽")[0]
#                     price = int("".join(filter(str.isdigit, price_text)))
#                     prices.append(price)
#             except (ValueError, AttributeError):
#                 self.logger.warning("Ошибка парсинга цены на Avito")
#
#         self.logger.info(f"Получено {len(prices)} цен с Avito")
#         return prices[:100]
#
