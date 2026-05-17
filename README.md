# Telegram Lead Funnel

Локальный MVP для поиска свежих Kwork-заказов на web-разработку.

Инструмент читает публичный Kwork-канал в Telegram, открывает страницу заказа на Kwork, отбрасывает Bitrix-заказы и проекты с большим числом откликов, отправляет лиды на email и дает готовый текст отклика для ручной отправки.

Если позже появятся `TELEGRAM_API_ID` и `TELEGRAM_API_HASH`, можно включить режим автоотправки после подтверждения `OK <lead_id>`. Без этих данных работает публичный read-only режим через `https://t.me/s/...`.

## Что умеет MVP

- `lead-funnel.cmd scan` — удобный запуск из Windows без переустановки пакета.
- `scan-now.cmd` — двойной клик для одного сканирования.
- `watch.cmd` — двойной клик для непрерывного мониторинга.
- `python -m app.main scan` — один раз прочитать каналы, создать лиды и отправить email.
- `python -m app.main approvals` — режим для будущей автоотправки через Telegram API. В public read-only режиме команда ничего не отправляет.
- `python -m app.main orders ...` — вести заказ после отклика: принять, взять в работу, отдать ТЗ в Codex, отправить результат на апрув вместе с готовым письмом заказчику.
- `python -m app.main order-reviews` — прочитать email-команды по заказам: `DONE <order_id>` или `FIX <order_id>: правки`.
- `python -m app.main watch` — циклически выполнять scan, approvals и order-reviews локально.

## Установка

```powershell
python -m pip install --upgrade pip
python -m pip install .[dev]
```

Если запускаешь команды из рабочей папки без переустановки пакета после правок, добавь текущий `src` в `PYTHONPATH`:

```powershell
$env:PYTHONPATH="src"
```

## Запуск из терминала

Самый удобный вариант на Windows:

```powershell
.\lead-funnel.cmd scan
.\lead-funnel.cmd watch
.\lead-funnel.cmd approvals
.\lead-funnel.cmd orders list
```

Для запуска двойным кликом:

- `scan-now.cmd` — один раз проверить источники и отправить новые лиды на почту.
- `watch.cmd` — оставить мониторинг включенным в открытом окне терминала.

## Настройка

1. Скопируй `.env.example` в `.env`.
2. Для текущей Kwork-only схемы оставь:
   - `TELEGRAM_CHANNELS=@freelance_dev_work`
   - можно указать `https://t.me/freelance_dev_work`, результат тот же.
3. Для режима без Telegram API оставь:
   - `TELEGRAM_API_ID=0`
   - `TELEGRAM_API_HASH=fill_later`
4. Заполни SMTP/IMAP доступы к почте.
5. Настрой лимит откликов:
   - `KWORK_MAX_RESPONSES=5` — отправлять только заказы, где на странице Kwork видно не больше 5 откликов.
6. Не коммить `.env`: файл уже исключен через `.gitignore`.

## Безопасный поток

1. Инструмент находит свежий пост из Kwork-канала.
2. Создает лид в SQLite.
3. Отправляет письмо с резюме, контактом, ссылкой и готовым текстом отклика.
4. Ты открываешь ссылку на пост или контакт.
5. Копируешь блок `СКОПИРОВАТЬ ОТКЛИК` и отправляешь его вручную.

Сейчас фильтр намеренно мягкий по тематике: из Kwork-ленты принимаются почти все заказы с ссылкой для отклика, кроме Bitrix/Битрикс. Но перед письмом инструмент открывает страницу заказа и проверяет число откликов через поле `workerCount`; если откликов больше `KWORK_MAX_RESPONSES` или число откликов не удалось прочитать, письмо не отправляется. Черновик отклика не просит у заказчика уточнения, доступы или макеты, а сразу предлагает взяться за задачу.

В public read-only режиме инструмент не может писать в Telegram сам и не пытается обрабатывать `OK`.

## Поток выполнения заказов

После успешной автоотправки отклика через Telegram API лид автоматически становится заказом. В ручном режиме заказ можно добавить самому:

```powershell
python -m app.main orders receive --contact "@client_dev" --title "Лендинг" --brief "Сверстать HTML/CSS/JS лендинг"
python -m app.main orders start 1
python -m app.main orders handoff 1
python -m app.main orders submit 1 --deliverable "Готовая ссылка: https://example.com"
python -m app.main order-reviews
python -m app.main orders list
```

Статусы заказа:

- `received` — заказ получен.
- `in_progress` — заказ взят в работу.
- `ready_for_approval` — результат отправлен на проверку; письмо содержит предложение/сообщение заказчику, собранное из ТЗ, результата и последних правок.
- `revision_requested` — пришли правки, нужно доработать и снова выполнить `orders submit`.
- `done` — заказ одобрен командой `DONE <order_id>`.

Команды в ответе на письмо с результатом:

- `DONE <order_id>` — принять работу и пометить заказ сделанным.
- `FIX <order_id>: что поправить` — вернуть заказ в правки.

## Передача заказа в Codex

Команда handoff создает markdown-файл с готовым заданием для Codex:

```powershell
python -m app.main orders handoff 1
```

По умолчанию файл создается в `handoffs/order-1-handoff.md`. В него попадают:

- ID, статус, контакт и даты заказа.
- ТЗ заказчика.
- Последние правки, если они есть.
- Последний результат, если заказ уже отдавался на проверку.
- Definition of Done и минимальная команда проверки.

Папка `handoffs/` исключена из git, потому что эти файлы могут содержать пользовательские детали заказа.

## Smoke-проверка

```powershell
python -m pytest -q
python -m app.main scan
python -m app.main orders list
```

Если `TELEGRAM_API_ID=0`, авторизация Telethon не нужна.
