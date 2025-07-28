## Требования
- Python 3.11 (проверено на версии 3.11.8).
- Пакеты из `requirements.txt`.
- Установленный Google Chrome (ChromeDriver загружается автоматически).

## Настройка
1. Создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Установите зависимости из файла requirements:
   ```bash
   pip install -r requirements.txt
   ```

Разработка ведётся в каталоге `src/`.

## Настройка ChromeDriver
Selenium использует бинарный файл [ChromeDriver](https://chromedriver.chromium.org/). Если путь к исполняемому файлу не задан, подходящая версия будет загружена автоматически. При необходимости можно указать свой путь через переменную окружения `CHROMEDRIVER_PATH` или передать его в `whatsapp_sender.start_driver()`.

Пример:
```bash
export CHROMEDRIVER_PATH=/opt/chromedriver
```

## Профиль WhatsApp Web
Чтобы сессия WhatsApp оставалась активной между запусками, создайте отдельный профиль Chrome и один раз войдите вручную. Запустите Chrome с нужным каталогом, откройте WhatsApp Web и отсканируйте QR‑код:
```bash
google-chrome --user-data-dir=/path/to/wa-profile https://web.whatsapp.com
```
Укажите переменную окружения ``CHROME_PROFILE_DIR`` на этот каталог (или передайте путь в ``send_message()``/``wait_for_reply()``) перед запуском бота:
```bash
export CHROME_PROFILE_DIR=/path/to/wa-profile
```

## База данных
Проект использует SQLite для хранения данных пользователей и исходящих сообщений. Чтобы создать локальную базу с примером данных, выполните:
```bash
python -m src.database
```
В корне проекта появится файл `database.sqlite3` с необходимыми таблицами.

## Настройка Zoom
Запросы к Zoom теперь используют OAuth (Server-to-Server). Создайте приложение в маркетплейсе Zoom и запишите значения **Client ID**, **Client Secret** и **Account ID**. Добавьте их в `config.json` или экспортируйте переменные окружения:
```json
{
  "zoom_client_id": "YOUR_CLIENT_ID",
  "zoom_client_secret": "YOUR_CLIENT_SECRET",
  "zoom_account_id": "YOUR_ACCOUNT_ID"
}
```
Названия переменных окружения: `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `ZOOM_ACCOUNT_ID`.

## Использование CLI
Проект предоставляет небольшую консольную утилиту с несколькими командами. Запускайте их через `python -m src.cli` и имя команды.
```bash
python -m src.cli send-messages phones.csv
python -m src.cli update-db
python -m src.cli stats
python -m src.cli survey phones.csv --workers 2
```
`send-messages` импортирует номера из CSV и начинает отправлять приветствие. `update-db` синхронизирует базу SQLite, создавая таблицы при необходимости. `stats` выводит, сколько сообщений отправлено и сколько ответов получено. `survey` запускает опрос для каждого номера из CSV. Опция ``--workers`` позволяет обрабатывать несколько номеров параллельно.

## Опрос
В `src/survey.py` реализован небольшой опросник, который собирает три ответа:

1. Возраст участника.
2. Уровень образования.
3. Пол.

Для квалификации используются только возраст и образование, но значение пола сохраняется вместе с остальными ответами на будущее.

Команда `survey` ожидает CSV‑файл с одним номером телефона в строке. Бот отправляет приветствие, задаёт вопросы и, если ответы подходят под критерии, присылает ссылку на встречу в Zoom.
