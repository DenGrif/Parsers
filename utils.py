import logging
from datetime import datetime
import random
import urllib.parse
import requests
from requests.exceptions import RequestException

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
]

PROXIES = [
    "http://proxy1:8080",
    "http://proxy2:8080",  # Добавьте свои прокси
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def get_random_proxy():
    return random.choice(PROXIES) if PROXIES else None

# Базовая функция запроса
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