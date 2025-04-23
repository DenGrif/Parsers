import os
import logging
import random
import requests
import time
from datetime import datetime, timedelta
from requests.exceptions import RequestException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def is_proxy_working(proxy_url, test_url="http://httpbin.org/ip", timeout=5):
    """Проверяет работоспособность одного прокси"""
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        response = requests.get(test_url, proxies=proxies, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def get_working_proxy(max_attempts=9):
    """
    Пытается найти рабочий прокси за указанное число попыток
    возвращает прокси в формате "ip:port@login:password" или None
    """
    logging.info("Начало проверки прокси...")
    try:
        # Загрузка прокси из файла с логированием
        try:
            with open(PROXY_FILE, "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
                logging.info(f"Прокси загружены из файла: {len(proxies)} шт.")

            if proxies:
                logging.info(f"Загружено {len(proxies)} прокси из файла {PROXY_FILE}")
                logging.info("Проверка прокси завершена.")
            else:
                logging.warning(f"Файл {PROXY_FILE} пуст — работа будет вестись с собственным IP")
                return None
        except FileNotFoundError:
            logging.warning(f"Файл {PROXY_FILE} не найден — работа будет вестись с собственным IP")
            return None

        # Поиск рабочего прокси
        for attempt in range(1, max_attempts + 1):
            proxy = random.choice(proxies)
            try:
                host_port, auth = proxy.split('@')
                username, password = auth.split(':')
                proxy_url = f"http://{username}:{password}@{host_port}"

                logging.info(f"Попытка {attempt}/{max_attempts}: проверка прокси {host_port}")

                if is_proxy_working(proxy_url):
                    logging.info(f"Найден рабочий прокси: {host_port}")
                    return proxy
                else:
                    logging.warning(f"Прокси {host_port} не отвечает")

            except Exception as e:
                logging.warning(f"Ошибка проверки прокси: {str(e)}")
                continue

        logging.warning(f"Не удалось найти рабочий прокси после {max_attempts} попыток")
        return None

    except Exception as e:
        logging.error(f"Критическая ошибка в get_working_proxy: {str(e)}")
        return None

# Файл с прокси
PROXY_FILE = "proxies.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


def make_screenshot(driver, filename_prefix="error"):
    """Создает скриншот с текущим timestamp"""
    try:
        timestamp = datetime.now().strftime("%d%m%Y__%H%M%S")
        screenshot_path = f"error/{filename_prefix}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"Скриншот сохранен: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"Не удалось сделать скриншот: {str(e)}")
        return None


def safe_request(url, headers=None, timeout=10, use_proxy=True, retries=3, use_own_ip=False):
    """Безопасный запрос HTML-страницы через requests с поддержкой прокси, сессий и повторных попыток."""

    logging.info(f"Начало safe_request: {url}")

    session = requests.Session()  # Сохраняет cookies между запросами
    proxy_used = False
    last_exception = None

    for attempt in range(1, retries + 1):
        try:
            # Задержка перед запросом для имитации реального пользователя
            time.sleep(random.uniform(3, 6))

            # Заголовки запроса
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.avito.ru/",
                "Connection": "keep-alive",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
            }

            proxies = None
            if use_own_ip:
                logging.info("Используется собственный IP.")
            elif use_proxy:
                proxy = get_working_proxy()
                if proxy:
                    try:
                        host_port, auth = proxy.split('@')
                        username, password = auth.split(':')
                        proxy_url = f"http://{username}:{password}@{host_port}"
                        proxies = {"http": proxy_url, "https": proxy_url}
                        logging.info(f"Попытка {attempt}/{retries} — используется прокси: {host_port}")
                        proxy_used = True
                    except Exception as e:
                        logging.warning(f"Ошибка разбора прокси {proxy}: {e}")
                        proxies = None

            response = session.get(url, headers=headers, proxies=proxies, timeout=timeout)

            if response.status_code == 429:
                logging.warning(f"Попытка {attempt}/{retries}: 429 Too Many Requests — ждём и повторяем...")
                time.sleep(random.uniform(30, 60))
                continue

            response.raise_for_status()
            logging.info(f"Успешный запрос к {url} за {response.elapsed.total_seconds():.2f} сек.")
            return response

        except RequestException as e:
            last_exception = e
            logging.warning(f"Попытка {attempt}/{retries} не удалась: {e}")
            time.sleep(2 ** attempt)

    # После всех попыток
    logging.error(f"Не удалось получить {url} после {retries} попыток. Последняя ошибка: {last_exception}")

    if proxy_used and not use_own_ip:
        logging.info("Переход на собственный IP после неудачи с прокси.")
        return safe_request(url, timeout=timeout, use_proxy=False, retries=retries, use_own_ip=True)

    return None



def selenium_request(url, driver, use_proxy=True, retries=3):
    """Загрузка HTML-страницы через Selenium для Auto.ru"""
    for attempt in range(retries + 1):
        try:
            proxy = get_working_proxy() if use_proxy else None

            if proxy:
                try:
                    # Разбиваем строку прокси на части: host:port@login:password
                    proxy_parts = proxy.split('@')
                    host_port = proxy_parts[0]
                    auth_part = proxy_parts[1]
                    username, password = auth_part.split(':')

                    # Формируем URL прокси с логином и паролем
                    proxy_url = f"http://{username}:{password}@{host_port}"

                    # Настройка прокси в ChromeOptions
                    options = Options()
                    options.add_argument("--headless")
                    options.add_argument("--ignore-certificate-errors")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--disable-features=SecureDns")
                    options.add_argument(
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    options.add_argument(f"--proxy-server={proxy_url}")

                    logging.info(f"Используется прокси: {proxy_url}")
                except Exception as e:
                    logging.error(f"Ошибка парсинга прокси {proxy}: {str(e)}")
                    proxy = None  # Пропускаем этот прокси
            else:
                logging.info("Используется собственный IP.") # после 3 не удачных попыток
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-features=SecureDns")
                options.add_argument(
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

            # Инициализация драйвера с текущими настройками
            if not driver:
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=options
                )

            start_time = time.time()
            driver.get(url)

            # Проверка на SSO-страницу
            if "sso.auto.ru" in driver.current_url:
                driver.find_element(By.TAG_NAME, "form").submit()
                time.sleep(2)  # Ждём редирект

            # Ожидание загрузки объявлений
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ListingItem"))
            )
            elapsed_time = time.time() - start_time
            logging.info(f"Запрос к {url} выполнен за {elapsed_time:.2f} сек.")

            return driver.page_source, driver, True  # Возвращаем True, если запрос успешен
        except Exception as e:
            if attempt < retries:
                logging.warning(
                    f"Попытка {attempt + 1}/{retries} для {url} через {proxy or 'собственный IP'}: {e}"
                )
                # Экспоненциальная задержка (1, 2, 4 секунды между попытками)
                delay = 2 ** attempt
                time.sleep(delay)
            else:
                logging.error(
                    f"Не удалось выполнить запрос к {url} после {retries} попыток: {str(e)}"
                )
                if proxy:
                    logging.info("Переходим к использованию собственного IP.")
                    return selenium_request(url, None, use_proxy=False, retries=retries)
                return "", None, False  # Возвращаем False, если запрос неуспешен
    return "", None, False  # Возвращаем False, если запрос неуспешен


def selenium_request_drom(url, driver, use_proxy=True, retries=3):
    """Загрузка HTML-страницы через Selenium для Drom.ru"""
    for attempt in range(retries + 1):
        try:
            proxy = get_working_proxy() if use_proxy else None

            if proxy:
                try:
                    # Разбиваем строку прокси на части: host:port@login:password
                    proxy_parts = proxy.split('@')
                    host_port = proxy_parts[0]
                    auth_part = proxy_parts[1]
                    username, password = auth_part.split(':')

                    # Формируем URL прокси с логином и паролем
                    proxy_url = f"http://{username}:{password}@{host_port}"

                    # Настройка прокси в ChromeOptions
                    options = webdriver.ChromeOptions()
                    options.add_argument("--headless")
                    options.add_argument("--ignore-certificate-errors")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--disable-features=SecureDns")
                    options.add_argument(
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    options.add_argument(f"--proxy-server={proxy_url}")

                    logging.info(f"Используется прокси: {proxy_url}")
                except Exception as e:
                    logging.error(f"Ошибка парсинга прокси {proxy}: {str(e)}")
                    proxy = None  # Пропускаем этот прокси
            else:
                logging.info("Используется собственный IP.") # после 3 не удачных попыток
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-features=SecureDns")
                options.add_argument(
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

            # Инициализация драйвера с текущими настройками
            if not driver:
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=options
                )

            start_time = time.time()
            driver.get(url)

            # Ожидание загрузки объявлений
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-ftid='bulls-list_bull']"))
            )
            logging.info(f"Запрос к {url} занял {time.time()-start_time:.3f} сек")

            #elapsed_time = time.time() - start_time
            #logging.info(f"Запрос к {url} выполнен за {elapsed_time:.2f} сек.")

            return driver.page_source, driver, True  # Возвращаем True, если запрос успешен
        except Exception as e:
            if attempt < retries:
                logging.warning(
                    f"Попытка {attempt + 1}/{retries} для {url} через {proxy or 'собственный IP'}: {e}"
                )
                # Экспоненциальная задержка (1, 2, 4 секунды между попытками)
                delay = 2 ** attempt
                time.sleep(delay)
            else:
                logging.error(
                    f"Не удалось выполнить запрос к {url} после {retries} попыток: {str(e)}"
                )
                if proxy:
                    logging.info("Переходим к использованию собственного IP.")
                    return selenium_request_drom(url, driver, use_proxy=False, retries=retries)
                return "", None, False  # Возвращаем False, если запрос неуспешен
    return "", None, False  # Возвращаем False, если запрос неуспешен

# Настройка логирования
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):  # Создаём папку, если её нет
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f"parser_log_{datetime.now().strftime('%Y-%m-%d__%H-%M')}.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True  # Принудительное обновление конфигурации
    )
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.info("Логирование настроено успешно!")  # Проверка, записывается ли лог


