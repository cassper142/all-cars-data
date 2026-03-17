# cars-data.com scraper (Playwright, async)

Скрипт собирает иерархию:

- Марка (brand)
- Модель (model)
- Поколение (generation)
- Модификации (modifications)

Для каждой модификации пытается найти самую “богатую” таблицу (по числу строк) и парсит её как `key -> value`, а также дополнительно вынимает поля `engine`, `power`, `body` эвристиками по названиям строк.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Запуск

Вариант 1 (рекомендуется): **авто‑поиск** страницы марок от главной:

```bash
python scrape_cars_data.py --base-url "https://www.cars-data.com/" --out cars-data.json --headless
```

Вариант 2: если авто‑поиск не сработал, укажите **страницу со списком марок/брендов** вручную:

```bash
python scrape_cars_data.py --start-url "https://cars-data.com/..." --out cars-data.json --headless
```

Лимиты (полезно для теста, чтобы не парсить всё сразу):

```bash
python scrape_cars_data.py \
  --base-url "https://www.cars-data.com/" \
  --out cars-data.sample.json \
  --max-brands 2 --max-models 2 --max-generations 2 --max-mods 5 \
  --headless
```

Паузы/таймауты:

```bash
python scrape_cars_data.py --start-url "https://cars-data.com/..." --min-pause 1.0 --max-pause 3.0 --timeout-ms 60000 --headless
```

## Выходной формат

`brands[].models[].generations[].modifications[]` содержит:

- `specs`: словарь из таблицы характеристик
- `extracted.engine`, `extracted.power`, `extracted.body`: основные поля, вытащенные эвристиками

