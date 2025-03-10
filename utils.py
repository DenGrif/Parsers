import logging
from datetime import datetime
import random
import requests
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from webdriver_manager.chrome import ChromeDriverManager


def selenium_request(url):
    driver = None  # Инициализируем driver как None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.get(url)

        # Проверка на SSO-страницу
        if "sso.auto.ru" in driver.current_url:
            # Имитация отправки формы
            form = driver.find_element(By.TAG_NAME, "form")
            form.submit()
            time.sleep(2)  # Ждём редиректа

        # Ждём загрузки данных
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ListingItem"))
            )
        except:
            pass

        html = driver.page_source
    except Exception as e:
        logging.error(f"Ошибка при работе с Selenium: {str(e)}")
        html = ""
    finally:
        if driver:  # Проверяем, что драйвер был инициализирован
            driver.quit()
    return html

# Логирование
def setup_logging():
    log_filename = f"logs/parser_log_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

# User-Agent и прокси
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
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
    # proxies = {"http": proxy, "https": proxy} if proxy else None
    proxies = None
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response
    except RequestException as e:
        logging.error(f"Ошибка при запросе к {url}: {str(e)}")
        return None
