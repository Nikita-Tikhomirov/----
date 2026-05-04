# Telegram Lead Funnel

Локальный MVP для поиска простых заказов на web-разработку в Telegram-каналах.

Инструмент читает заданные публичные Telegram-каналы через user session, отбирает простые задачи по HTML/CSS/JS и WordPress без React и конструкторов, отправляет лиды на email и отправляет отклик заказчику только после подтверждения ответом `OK <lead_id>`.

## Что умеет MVP

- `python -m app.main scan` — один раз прочитать каналы, создать лиды и отправить email.
- `python -m app.main approvals` — прочитать email-ответы `OK <lead_id>` и отправить одобренные отклики в Telegram.
- `python -m app.main watch` — циклически выполнять scan и approvals локально.

## Установка

```powershell
python -m pip install --upgrade pip
python -m pip install --use-feature=in-tree-build .[dev]
```

Флаг `--use-feature=in-tree-build` нужен для старых версий pip и путей с кириллицей.

## Настройка

1. Скопируй `.env.example` в `.env`.
2. Заполни Telegram API credentials:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_SESSION_NAME`
   - `TELEGRAM_CHANNELS`
3. Заполни SMTP/IMAP доступы к почте.
4. Не коммить `.env`: файл уже исключен через `.gitignore`.

## Безопасный поток

1. Инструмент находит подходящий пост.
2. Создает лид в SQLite.
3. Отправляет письмо с резюме, контактом, ссылкой и черновиком отклика.
4. Ты отвечаешь на письмо строкой `OK <lead_id>`.
5. Только после этого инструмент отправляет отклик в Telegram.

Повторная отправка по одному lead id блокируется таблицей `sent_messages`.

## Smoke-проверка

```powershell
python -m pytest -q
python -m app.main scan
python -m app.main approvals
```

Первый запуск Telethon может запросить авторизацию Telegram-аккаунта в терминале.
