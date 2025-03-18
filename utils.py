import logging
from datetime import datetime
import random
import requests
from requests.exceptions import RequestException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def selenium_request(url, driver):
    """Функция для загрузки HTML-страницы через Selenium для auto.ru"""
    try:
        driver.get(url)

        # Проверка на SSO-страницу
        if "sso.auto.ru" in driver.current_url:
            form = driver.find_element(By.TAG_NAME, "form")
            form.submit()
            time.sleep(2)  # Ждём редиректа

        # Ожидание загрузки объявлений
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ListingItem"))
        )
        html = driver.page_source
        logging.debug("HTML-код успешно загружен.")  # Вместо огромного HTML-файла
        return html

    except Exception as e:
        logging.error(f"Ошибка при работе с Selenium: {str(e)}")
        return ""


def selenium_request_drom(url, driver):
    """Функция для загрузки HTML-страницы через Selenium для Drom.ru."""
    try:
        driver.get(url)
        # Ждём загрузки данных
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-ftid='bulls-list_bull']"))
        )
        html = driver.page_source
        logging.debug("HTML-код успешно загружен.")  # Вместо огромного HTML-файла
        return html

    except Exception as e:
        logging.error(f"Ошибка при работе с Selenium для Drom.ru: {str(e)}")
    return ""


# Логирование
def setup_logging():
    log_filename = f"logs/parser_log_{datetime.now().strftime('%Y-%m-%d__%H-%M')}.log"
    logging.basicConfig(
        level=logging.DEBUG,  # Уровень логирования DEBUG
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),  # Запись в новый файл,
            logging.StreamHandler()
        ]
    )

# Отключаем логи Selenium и urllib3, которые пишут HTML-страницы
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# User-Agent и прокси
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Можно добавить ещё User-Agent
]

PROXIES = [
    # "http://login1:pass1@proxy1.example.com:8080",
    # "http://login2:pass2@proxy2.example.com:8080",  # Можно добавить ещё прокси
]


def get_random_user_agent():
    return random.choice(USER_AGENTS)


def get_random_proxy():
    return random.choice(PROXIES) if PROXIES else None


def safe_request(url, headers=None, proxy=None, timeout=10):
    if headers is None:
        headers = {}
    headers.update({
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    })
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response
    except RequestException as e:
        logging.error(f"Ошибка при запросе к {url}: {str(e)}")
        return None
