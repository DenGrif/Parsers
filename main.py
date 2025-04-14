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

    if args.limit < 10 or args.limit > 100:
        print("Ошибка: Количество цен должно быть в диапазоне от 10 до 100.")
        return

    make, model, year, limit = args.make, args.model, args.year, args.limit

    sanitized_make = re.sub(r'[^a-zA-Z0-9]', '_', make.lower())
    sanitized_model = re.sub(r'[^a-zA-Z0-9]', '_', model.lower())

    # Создаем общий объект Event для остановки парсеров
    stop_event = Event()
    found_prices = []
    lock = Lock()

    # Инициализация парсеров без локального лимита
    parsers = [
        AvitoParser(normalize_make(make, "avito.ru"), model, year, stop_event, found_prices, lock, limit=limit, use_proxy=True),
        AutoRuParser(normalize_make(make, "auto.ru"), model, year, stop_event, found_prices, lock, limit=limit, use_proxy=True),
        DromParser(normalize_make(make, "drom.ru"), model, year, stop_event, found_prices, lock, limit=limit, use_proxy=True)
    ]

    # Многопоточный парсинг
    threads = [threading.Thread(target=parser.parse) for parser in parsers]
    for t in threads:
        t.start()

    # Ждем завершения всех потоков
    for t in threads:
        t.join()

    # Логируем общее количество найденных цен
    logging.info(f"Всего найдено цен: {len(found_prices)}")

    # Если меньше лимита цен:
    if len(found_prices) < limit:
        logging.warning(f"Собрано меньше {limit} цен: {len(found_prices)}")

    # Расчёт залоговой стоимости
    result = calculate_collateral(found_prices[:limit])
    output = {
        "make": make,
        "model": model,
        "year": year,
        "limit": limit,
        "cars_parsed": len(found_prices[:limit]),  # Учитываем только лимит
        **result
    }

    # Сохранение результатов
    filename = f"data/{datetime.now().strftime('%d-%m-%Y__%H-%M')}_{sanitized_make}_{sanitized_model}_{'_'.join(map(str, year))}_results.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(json.dumps(output, indent=4, ensure_ascii=False))

    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Окончание скрипта: {end_time.strftime('%d-%m-%Y %H:%M:%S')}")
    minutes, seconds = divmod(duration.total_seconds(), 60)
    logging.info(f"Время выполнения скрипта: {int(minutes)} мин : {int(seconds):02d},{str(duration.microseconds)[:2]} сек")


if __name__ == "__main__":
    main()

