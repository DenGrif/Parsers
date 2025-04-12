import re
import argparse
import json
import threading
import logging
from calculator import calculate_collateral
from datetime import datetime
from parsers import AvitoParser, AutoRuParser, DromParser
from utils import setup_logging  # логирование
from threading import Event, Lock


# Фильтр для отечественного авто, пишем lada, а на каждый сайт уходит своё название
def normalize_make(make, site):
    mapping = {
        "avito.ru": {"lada": "vaz_lada"},
        "auto.ru": {"lada": "vaz"},
        "drom.ru": {"lada": "lada"},
    }
    return mapping.get(site, {}).get(make.lower(), make.lower())


def main():
    setup_logging()

    start_time = datetime.now()
    logging.info(f"Старт скрипта: {start_time.strftime('%d-%m-%Y %H:%M:%S')}")

    parser = argparse.ArgumentParser(description="Расчет залоговой стоимости автомобиля")
    parser.add_argument("--make", required=True, help="Марка автомобиля")
    parser.add_argument("--model", required=True, help="Модель автомобиля")
    parser.add_argument("--year", nargs='+', type=int, help="Год выпуска автомобиля или диапазон годов (например: 2020 или 2019 2021)")
    parser.add_argument("--limit", type=int, default=100, help="Количество цен для парсинга (от 10 до 100)")
    args = parser.parse_args()

    # Фильтр диапазона поиска цен
    if args.limit < 10 or args.limit > 100:
        print("Ошибка: Количество цен должно быть в диапазоне от 10 до 100.")
        return

    make, model, year, limit = args.make, args.model, args.year, args.limit

    # Очистка названия от нежелательных символов
    sanitized_make = re.sub(r'[^a-zA-Z0-9]', '_', make.lower())
    sanitized_model = re.sub(r'[^a-zA-Z0-9]', '_', model.lower())

    # Инициализация парсеров
    parsers = [
        AvitoParser(normalize_make(make, "avito.ru"), model, year, limit, use_proxy=True),
        AutoRuParser(normalize_make(make, "auto.ru"), model, year, limit, use_proxy=True),
        DromParser(normalize_make(make, "drom.ru"), model, year, limit, use_proxy=True)
    ]

    # Многопоточный парсинг
    results = []
    threads = []
    for parser in parsers:
        t = threading.Thread(target=lambda p=parser: results.append(p.parse()))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Объединение цен (задаётся в параметре limit от 10 до 100)
    all_prices = []
    for res in results:
        all_prices.extend(res[:limit])
    all_prices = all_prices[:limit]

    # Если меньше 100 цен:
    if len(all_prices) < limit:
        logging.warning(f"Собрано меньше {limit} цен: {len(all_prices)}")

    # Расчёт залоговой стоимости
    result = calculate_collateral(all_prices)
    output = {
        "make": make,
        "model": model,
        "year": year,
        "limit": limit,
        **result
    }

    # Формирование имени файла с датой, маркой, моделью и годом
    filename = f"data/{datetime.now().strftime('%d-%m-%Y__%H-%M')}_{sanitized_make}_{sanitized_model}_{'_'.join(map(str, year))}_results.json"
    # Сохранение в JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    # Вывод в консоль
    print(json.dumps(output, indent=4, ensure_ascii=False))

    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Окончание скрипта: {end_time.strftime('%d-%m-%Y %H:%M:%S')}")
    minutes, seconds = divmod(duration.total_seconds(), 60)
    logging.info(f"Время выполнения скрипта: {int(minutes)} мин : {int(seconds):02d},{str(duration.microseconds)[:2]} сек")

if __name__ == "__main__":
    main()



# попытка одного счётчика
# import re
# import argparse
# import json
# import threading
# import logging
# from calculator import calculate_collateral
# from datetime import datetime
# from parsers import AvitoParser, AutoRuParser, DromParser
# from utils import setup_logging  # логирование
# from threading import Event, Lock
#
#
# # Фильтр для отечественного авто, пишем lada, а на каждый сайт уходит своё название
# def normalize_make(make, site):
#     mapping = {
#         "avito.ru": {"lada": "vaz_lada"},
#         "auto.ru": {"lada": "vaz"},
#         "drom.ru": {"lada": "lada"},
#     }
#     return mapping.get(site, {}).get(make.lower(), make.lower())
#
#
# def main():
#     setup_logging()
#     start_time = datetime.now()
#     logging.info(f"Старт скрипта: {start_time.strftime('%d-%m-%Y %H:%M:%S')}")
#     parser = argparse.ArgumentParser(description="Расчет залоговой стоимости автомобиля")
#     parser.add_argument("--make", required=True, help="Марка автомобиля")
#     parser.add_argument("--model", required=True, help="Модель автомобиля")
#     parser.add_argument("--year", nargs='+', type=int,
#                         help="Год выпуска автомобиля или диапазон годов (например: 2020 или 2019 2021)")
#     parser.add_argument("--limit", type=int, default=100, help="Количество цен для парсинга (от 10 до 100)")
#     args = parser.parse_args()
#
#     # Фильтр диапазона поиска цен
#     if args.limit < 10 or args.limit > 100:
#         print("Ошибка: Количество цен должно быть в диапазоне от 10 до 100.")
#         return
#
#     make, model, year, limit = args.make, args.model, args.year, args.limit
#     # Очистка названия от нежелательных символов
#     sanitized_make = re.sub(r'[^a-zA-Z0-9]', '_', make.lower())
#     sanitized_model = re.sub(r'[^a-zA-Z0-9]', '_', model.lower())
#     # Инициализация парсеров
#     parsers = [
#         AvitoParser(normalize_make(make, "avito.ru"), model, year, use_proxy=True),
#         AutoRuParser(normalize_make(make, "auto.ru"), model, year, use_proxy=True),
#         DromParser(normalize_make(make, "drom.ru"), model, year, use_proxy=True)
#     ]
#
#     # Многопоточный парсинг
#     results = []
#     threads = []
#     collected_prices = 0
#     collected_prices_lock = Lock()
#     stop_event = Event()
#
#     def thread_target(parser):
#         nonlocal collected_prices
#         parser_results = parser.parse(collected_prices, collected_prices_lock, stop_event, limit)
#         with collected_prices_lock:
#             results.append(parser_results)
#             collected_prices += len(parser_results)
#             logging.info(f"Всего цен в collected_prices: {collected_prices}")
#
#     for parser in parsers:
#         t = threading.Thread(target=thread_target, args=(parser,))
#         threads.append(t)
#         t.start()
#
#     for t in threads:
#         t.join()
#
#     # Объединение цен (уже собрано нужное количество)
#     all_prices = []
#     for res in results:
#         all_prices.extend(res)
#     all_prices = all_prices[:limit]
#
#     # Если меньше 100 цен:
#     if len(all_prices) < limit:
#         logging.warning(f"Собрано меньше {limit} цен: {len(all_prices)}")
#
#     # Расчёт залоговой стоимости
#     result = calculate_collateral(all_prices)
#     output = {
#         "make": make,
#         "model": model,
#         "year": year,
#         "limit": limit,
#         **result
#     }
#
#     # Формирование имени файла с датой, маркой, моделью и годом
#     filename = f"data/{datetime.now().strftime('%d-%m-%Y__%H-%M')}_{sanitized_make}_{sanitized_model}_{'_'.join(map(str, year))}_results.json"
#     # Сохранение в JSON
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(output, f, indent=4, ensure_ascii=False)
#
#     # Вывод в консоль
#     print(json.dumps(output, indent=4, ensure_ascii=False))
#
#     end_time = datetime.now()
#     duration = end_time - start_time
#     logging.info(f"Окончание скрипта: {end_time.strftime('%d-%m-%Y %H:%M:%S')}")
#     minutes, seconds = divmod(duration.total_seconds(), 60)
#     logging.info(
#         f"Время выполнения скрипта: {int(minutes)} мин : {int(seconds):02d},{str(duration.microseconds)[:2]} сек")
#     logging.info(f"Всего найдено цен: {len(all_prices)}")  # Добавляем логирование общего количества найденных цен
#     logging.info(f"Всего цен в {collected_prices} collected_prices")
#
#
# if __name__ == "__main__":
#     main()




# тоn же
# import re
# import argparse
# import json
# import threading
# import logging
# from calculator import calculate_collateral
# from datetime import datetime
# from parsers import AvitoParser, AutoRuParser, DromParser
# from utils import setup_logging  # логирование
# from threading import Event, Lock
#
#
# # Фильтр для отечественного авто, пишем lada, а на каждый сайт уходит своё название
# def normalize_make(make, site):
#     mapping = {
#         "avito.ru": {"lada": "vaz_lada"},
#         "auto.ru": {"lada": "vaz"},
#         "drom.ru": {"lada": "lada"},
#     }
#     return mapping.get(site, {}).get(make.lower(), make.lower())
#
#
# def main():
#     setup_logging()
#     start_time = datetime.now()
#     logging.info(f"Старт скрипта: {start_time.strftime('%d-%m-%Y %H:%M:%S')}")
#     parser = argparse.ArgumentParser(description="Расчет залоговой стоимости автомобиля")
#     parser.add_argument("--make", required=True, help="Марка автомобиля")
#     parser.add_argument("--model", required=True, help="Модель автомобиля")
#     parser.add_argument("--year", nargs='+', type=int,
#                         help="Год выпуска автомобиля или диапазон годов (например: 2020 или 2019 2021)")
#     parser.add_argument("--limit", type=int, default=100, help="Количество цен для парсинга (от 10 до 100)")
#     args = parser.parse_args()
#
#     # Фильтр диапазона поиска цен
#     if args.limit < 10 or args.limit > 100:
#         print("Ошибка: Количество цен должно быть в диапазоне от 10 до 100.")
#         return
#
#     make, model, year, limit = args.make, args.model, args.year, args.limit
#     # Очистка названия от нежелательных символов
#     sanitized_make = re.sub(r'[^a-zA-Z0-9]', '_', make.lower())
#     sanitized_model = re.sub(r'[^a-zA-Z0-9]', '_', model.lower())
#     # Инициализация парсеров
#     parsers = [
#         AvitoParser(normalize_make(make, "avito.ru"), model, year, limit, use_proxy=True),
#         AutoRuParser(normalize_make(make, "auto.ru"), model, year, limit, use_proxy=True),
#         DromParser(normalize_make(make, "drom.ru"), model, year, limit, use_proxy=True)
#     ]
#
#     # Многопоточный парсинг
#     results = []
#     threads = []
#     collected_prices = 0
#     collected_prices_lock = Lock()
#     stop_event = Event()
#
#     def thread_target(parser):
#         nonlocal collected_prices
#         parser_results = parser.parse(collected_prices, collected_prices_lock, stop_event)
#         with collected_prices_lock:
#             results.append(parser_results)
#             collected_prices += len(parser_results)
#             if collected_prices >= limit:
#                 stop_event.set()
#
#     for parser in parsers:
#         t = threading.Thread(target=thread_target, args=(parser,))
#         threads.append(t)
#         t.start()
#
#     for t in threads:
#         t.join()
#
#     # Объединение цен (уже собрано нужное количество)
#     all_prices = []
#     for res in results:
#         all_prices.extend(res)
#     all_prices = all_prices[:limit]
#
#     # Если меньше 100 цен:
#     if len(all_prices) < limit:
#         logging.warning(f"Собрано меньше {limit} цен: {len(all_prices)}")
#
#     # Расчёт залоговой стоимости
#     result = calculate_collateral(all_prices)
#     output = {
#         "make": make,
#         "model": model,
#         "year": year,
#         "limit": limit,
#         **result
#     }
#
#     # Формирование имени файла с датой, маркой, моделью и годом
#     filename = f"data/{datetime.now().strftime('%d-%m-%Y__%H-%M')}_{sanitized_make}_{sanitized_model}_{'_'.join(map(str, year))}_results.json"
#     # Сохранение в JSON
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(output, f, indent=4, ensure_ascii=False)
#
#     # Вывод в консоль
#     print(json.dumps(output, indent=4, ensure_ascii=False))
#
#     end_time = datetime.now()
#     duration = end_time - start_time
#     logging.info(f"Окончание скрипта: {end_time.strftime('%d-%m-%Y %H:%M:%S')}")
#     minutes, seconds = divmod(duration.total_seconds(), 60)
#     logging.info(
#         f"Время выполнения скрипта: {int(minutes)} мин : {int(seconds):02d},{str(duration.microseconds)[:2]} сек")
#     logging.info(f"Всего найдено цен: {len(all_prices)}")  # Добавляем логирование общего количества найденных цен
#     logging.info(f"Всего цен в {collected_prices} collected_prices")
#
#
# if __name__ == "__main__":
#     main()





# import argparse
# import json
# import threading
# import logging
# from threading import Event, Lock
# from calculator import calculate_collateral
# from datetime import datetime
# from parsers import AvitoParser, AutoRuParser, DromParser
# import re
# from utils import setup_logging
#
#
# def normalize_make(make, site):
#     mapping = {
#         "avito.ru": {"lada": "vaz_lada"},
#         "auto.ru": {"lada": "vaz"},
#         "drom.ru": {"lada": "lada"},
#     }
#     return mapping.get(site, {}).get(make.lower(), make.lower())
#
#
# def main():
#     setup_logging()
#     start_time = datetime.now()
#     logging.info(f"Старт скрипта: {start_time.strftime('%d-%m-%Y %H:%M:%S')}")
#
#     parser = argparse.ArgumentParser(description="Расчет залоговой стоимости автомобиля")
#     parser.add_argument("--make", required=True, help="Марка автомобиля")
#     parser.add_argument("--model", required=True, help="Модель автомобиля")
#     parser.add_argument("--year", nargs='+', type=int,
#                         help="Год выпуска автомобиля или диапазон годов (например: 2020 или 2019 2021)")
#     parser.add_argument("--limit", type=int, default=100, help="Количество цен для парсинга (от 10 до 100)")
#     args = parser.parse_args()
#
#     if args.limit < 10 or args.limit > 100:
#         print("Ошибка: Количество цен должно быть в диапазоне от 10 до 100.")
#         return
#
#     make, model, year, limit = args.make, args.model, args.year, args.limit
#     sanitized_make = re.sub(r'[^a-zA-Z0-9]', '_', make.lower())
#     sanitized_model = re.sub(r'[^a-zA-Z0-9]', '_', model.lower())
#
#     # Общие ресурсы для потоков
#     shared_prices = []
#     prices_lock = Lock()
#     stop_event = Event()
#
#     # Функция для запуска в потоках
#     def run_parser(parser):
#         nonlocal shared_prices
#         try:
#             prices = parser.parse()
#             with prices_lock:
#                 if len(shared_prices) < limit:
#                     remaining = limit - len(shared_prices)
#                     shared_prices.extend(prices[:remaining])
#
#                     # Останавливаем все парсеры при достижении лимита
#                     if len(shared_prices) >= limit:
#                         for p in parsers:
#                             if hasattr(p, 'stop'):
#                                 p.stop()
#                                 logging.info(f"Отправлена команда остановки {p.__class__.__name__}")
#         except Exception as e:
#             logging.error(f"Ошибка в парсере {parser.__class__.__name__}: {str(e)}")
#
#     # Инициализация парсеров с передачей stop_event
#     parsers = [
#         AvitoParser(normalize_make(make, "avito.ru"), model, year, limit, use_proxy=True),
#         AutoRuParser(normalize_make(make, "auto.ru"), model, year, limit, use_proxy=True),
#         #DromParser(normalize_make(make, "drom.ru"), model, year, limit, use_proxy=True)
#     ]
#
#     for parser in parsers:
#         parser.stop_event = stop_event
#
#     # Запуск потоков
#     threads = []
#     for parser in parsers:
#         thread = threading.Thread(target=run_parser, args=(parser,))
#         thread.start()
#         threads.append(thread)
#
#     # Ожидание завершения с проверкой флага
#     while not stop_event.is_set():
#         for t in threads:
#             t.join(timeout=0.5)
#
#     # Принудительное завершение при необходимости
#     if stop_event.is_set():
#         for parser in parsers:
#             if hasattr(parser, 'stop'):
#                 parser.stop()
#
#     # Финализация результатов
#     result_prices = shared_prices[:limit]
#     if len(result_prices) < limit:
#         logging.warning(f"Собрано только {len(result_prices)} из {limit} цен")
#
#     result = calculate_collateral(result_prices)
#     output = {
#         "make": make,
#         "model": model,
#         "year": year,
#         "limit": limit,
#         **result
#     }
#
#     # Формирование имени файла с датой, маркой, моделью и годом
#     filename = f"data/{datetime.now().strftime('%d-%m-%Y__%H-%M')}_{sanitized_make}_{sanitized_model}_{'_'.join(map(str, year))}_results.json"
#     # Сохранение в JSON
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(output, f, indent=4, ensure_ascii=False)
#
#     # Вывод в консоль
#     print(json.dumps(output, indent=4, ensure_ascii=False))
#
#     end_time = datetime.now()
#     duration = end_time - start_time
#     minutes, seconds = divmod(duration.total_seconds(), 60)
#     logging.info(f"Время выполнения: {int(minutes)} мин {int(seconds)} сек")
#
#
# if __name__ == "__main__":
#     main()


# рабочий, по старому


