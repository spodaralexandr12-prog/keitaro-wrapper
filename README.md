# Keitaro Wrapper

Веб-приложение для управления кампаниями Keitaro через Admin API.

## Возможности

- Создание кампаний с указанием названия, GEO и ID оффера.
- Автоматическое создание двух потоков:
  - `GOOGLE_REDIRECT` — перенаправление посетителей из указанной страны на Google.
  - `OFFER_REDIRECT` — поток по умолчанию с выбранным оффером.
- Добавление офферов в поток.
- Удаление офферов из потока.
- Хранение информации о созданных кампаниях в SQLite.
- Управление структурой базы данных через Alembic.

## Технологии

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Alembic
- Keitaro Admin API

## Установка

1. Клонировать репозиторий:

```bash
git clone <URL_REPOSITORY>
cd keitaro-wrapper
```

2. Создать виртуальное окружение:

```bash
python -m venv venv
```

3. Активировать его в Windows:

```bash
venv\Scripts\activate
```

4. Установить зависимости:

```bash
pip install -r requirements.txt
```

## Настройка

Создать файл `.env` в корне проекта:

```env
KEITARO_URL=https://your-keitaro-domain.com
KEITARO_API_KEY=your_api_key
KEITARO_DOMAIN_ID=your_domain_id
KEITARO_GROUP_ID=your_group_id
KEITARO_TRAFFIC_SOURCE_ID=your_traffic_source_id
```

Указать собственные параметры Keitaro.

## Миграции базы данных

Применить миграции:

```bash
alembic upgrade head
```

Создать новую миграцию после изменения моделей:

```bash
alembic revision --autogenerate -m "migration description"
alembic upgrade head
```

## Запуск

```bash
uvicorn main:app --reload
```

Веб-интерфейс:

http://127.0.0.1:8000

Документация API:

http://127.0.0.1:8000/docs

## Безопасность

- Не публиковать файл `.env`.
- Не размещать API-ключи в репозитории.
- Не добавлять виртуальное окружение в Git.