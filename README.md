# Проект: Парсер цен автомобилей с сайтов

## Описание проекта

Этот проект представляет собой бэкэнд-скрипт на Python, который автоматически собирает данные о 
стоимости автомобилей с различных сайтов (avito.ru, auto.ru, drom.ru), 
рассчитывает среднюю стоимость и определяет залоговую стоимость по заданной формуле. 
Проект разработан для работы в Docker-контейнере (опционально).

## Цель разработки

Цель проекта — разработать скрипт, который будет:
1. Парсить данные о ценах на автомобили с различных сайтов.
2. Рассчитывать среднюю стоимость автомобиля.
3. Определять залоговую стоимость по формуле: `Залоговая стоимость = (Средняя стоимость 100 автомобилей) * 0.8`.

## Формула расчета

Залоговая стоимость автомобиля рассчитывается по формуле:
Залоговая стоимость = (Средняя стоимость 100 автомобилей) * 0.8
Средняя стоимость определяется как:
Средняя стоимость = Сумма цен 100 автомобилей / 100


## Источники данных

- **avito.ru** (раздел авто)
- **auto.ru**
- **drom.ru**

## Функционал:

### 1. Парсинг данных
- Скрипт подключается к сайтам-источникам.
- Запрашивает данные по заданной марке и модели автомобиля.
- Извлекает цену автомобиля.
- Сохраняет полученные данные в JSON файл.

### 2. Расчет залоговой стоимости
- После получения цен 100 автомобилей по каждой модели, выполняется расчет средней цены.
- От средней цены автоматически отнимается 20% — это и есть залоговая стоимость.

### 3. Обработка исключений
- Если не удалось получить данные с какого-либо сайта (сайт недоступен, капча, блокировка IP), это логируется.
- При получении менее 100 автомобилей по одной модели скрипт продолжает работать, но расчет производится на основе имеющихся данных с пометкой об этом.

## Технические требования

- **Язык разработки:** Python 3.13
- **Используемые библиотеки:** `requests`, `BeautifulSoup`, `pandas`, `logging`, `json` `Silenium`.
- **Поддержка многопоточности** для ускорения парсинга.
- **Логирование всех операций** (успех, ошибки, предупреждения).
- Возможность запуска через команду в терминале с передачей параметров:
  ```bash
  python collateral_calculator.py --make BMW --model X5

## Установка и запуск

1. Установка зависимостей
Для установки необходимых зависимостей выполните команду:
    ```bash
    pip install -r requirements.txt

2. Запуск скрипта
Для запуска скрипта используйте команду:
    ```bash 
    python main.py --make <марка автомобиля> --model <модель автомобиля>

* .Пример:
    ```bash
    python main.py --make BMW --model X5

3. Логирование.
Логи работы скрипта сохраняются в папке logs/ в файле с именем parser_log_YYYY-MM-DD.log.


4. Результаты
Результаты работы скрипта сохраняются в папке data/ в формате JSON. Имя файла формируется на основе даты, марки и модели автомобиля.

* Пример вывода
После успешного выполнения скрипта, вы получите JSON-файл с результатами:
    ```json
  {
  "make": "BMW",
  "model": "X5",
  "average_price": 3250000,
  "collateral_value": 2600000,
  "cars_parsed": 100
  }

Лицензия.
Этот проект распространяется под лицензией MIT.

Автор 
[DenGrif](https://github.com/DenGrif)

Контакты:
Если у вас есть вопросы или предложения, 
свяжитесь со мной по адресу: [grifon991@gmail.com](mailto:grifon991@gmail.com).

[Мой Telegram](https://t.me/DenGrifon)


