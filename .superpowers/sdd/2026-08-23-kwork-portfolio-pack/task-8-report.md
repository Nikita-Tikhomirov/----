# Task 8 Report: Manifest, Validation, Gallery, Domain Check, And CLI

Дата: 2026-08-23
Ветка: `codex/kwork-portfolio-pack`
Режим: `CLOUD_ONLY`
Commit: `feat: validate and package Kwork portfolio`
Push: не выполнялся по прямому указанию пользователя.
Публикация: не выполнялась; CLI не содержит команды публикации.

## Результат

Созданы пять модулей Task 8:

- `manifest.py` пишет стабильные `upload-manifest.json` в UTF-8 и `upload-manifest.csv` в `utf-8-sig`, сохраняя порядок каталога и четырех изображений;
- `validate.py` проверяет наличие, PNG-формат, размер 1920x1280, лимит 10 000 000 байт и отсутствие любых лишних PNG внутри каталога проекта;
- `gallery.py` создает локальный `gallery.html` с 15 unframed sections, четырьмя thumbnails формата 3:2 и состоянием валидации, не изменяя PNG;
- `domain_check.py` выполняет injectable DNS-проверку, удаляет дубли IPv4/IPv6, считает любой найденный адрес коллизией и обрабатывает как свободный домен только `socket.gaierror`;
- `cli.py` предоставляет `domains --check`, `validate-assets`, `render`, `manifest`, `validate` и `gallery`, возвращает ненулевой код при ошибках и выводит русские diagnostics в явно настроенном UTF-8.

Пути изображений в JSON, CSV, gallery и validation diagnostics формируются детерминированно с `/`, включая запуск на Windows. Asset inventory и Playwright renderer переиспользуются напрямую; site renderers и generated artifacts в Task 8 не изменялись.

## TDD

Первый RED:

```text
python -m pytest tests/test_portfolio_manifest.py tests/test_portfolio_validation.py tests/test_portfolio_domain_check.py -q
3 collection errors: ModuleNotFoundError для отсутствующего portfolio.kwork_pack.cli
```

Первый GREEN:

```text
16 passed in 2.23s
```

Интеграционная проверка выявила Windows stdout в `cp1251`. Отдельный subprocess test подтвердил RED через `UnicodeDecodeError`; после явного `sys.stdout`/`sys.stderr` UTF-8 он прошел, а реальная CLI-команда стала читаемой.

Дополнительный RED зафиксировал пропуск вложенного лишнего PNG. После рекурсивной проверки точных относительных путей оба unexpected-PNG теста прошли.

Итоговый focused GREEN:

```text
18 passed in 2.54s
```

## Реальные локальные данные

Проверка выполнялась только на чтение:

- asset inventory: `15 из 15`, отсутствуют `0`;
- `tochka-hoda`: проверены четыре существующих render output;
- validation: `files_checked=4`, `issues=0`;
- SHA-256 четырех PNG получен до завершения проверки; файлы не переписывались.

## Финальная проверка

```text
focused Task 8: 18 passed
all portfolio tests: 115 passed, 372 deselected
full pytest: 487 passed in 13.03s
python -m compileall -q src portfolio tests: exit 0
git diff --check: exit 0
mojibake scan: no matches
global harness smoke: ok, CLOUD_ONLY, Ollama commands skipped
```

Первый полный pytest один раз получил внешний `TargetClosedError` при запуске установленного Chrome с Windows exit code `3221225477`. Немедленный targeted Chrome smoke прошел (`1 passed`), затем два свежих полных suite прошли полностью (`487 passed` каждый); изменения renderer для этого не выполнялись.
