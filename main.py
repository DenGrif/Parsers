import argparse
import json
import threading
import logging
from calculator import calculate_collateral
from datetime import datetime
from utils import setup_logging
from parsers import AvitoParser, AutoRuParser, DromParser
import re


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Расчет залоговой стоимости автомобиля")
    parser.add_argument("--make", required=True, help="Марка автомобиля")
    parser.add_argument("--model", required=True, help="Модель автомобиля")
    parser.add_argument("--year", type=int, help="Год выпуска автомобиля")
    args = parser.parse_args()

    make, model = args.make, args.model
    year = args.year

    # Очистка названия от нежелательных символов
    sanitized_make = re.sub(r'[^a-zA-Z0-9]', '_', make.lower())
    sanitized_model = re.sub(r'[^a-zA-Z0-9]', '_', model.lower())

    # Инициализация парсеров
    parsers = [
        AvitoParser(make, model, year),
        AutoRuParser(make, model, year),
        DromParser(make, model, year)
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

    # Объединение цен (максимум 100 от каждого источника)
    all_prices = []
    for res in results:
        all_prices.extend(res[:100])
    all_prices = all_prices[:100]  # Общее ограничение в 100 цен

    # Если меньше 100 цен:
    if len(all_prices) < 100:
        logging.warning(f"Собрано меньше 100 цен: {len(all_prices)}")

    # Расчёт залоговой стоимости
    result = calculate_collateral(all_prices)
    output = {
        "make": make,
        "model": model,
        "year": year,
        **result
    }

    # Формирование имени файла с датой, маркой, моделью и годом
    filename = f"data/{datetime.now().strftime('%d-%m-%Y__%H-%M')}_{sanitized_make}_{sanitized_model}_{year}_results.json"

    # Сохранение в JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    # Вывод в консоль
    print(json.dumps(output, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
