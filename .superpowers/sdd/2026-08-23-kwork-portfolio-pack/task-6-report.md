# Task 6 Report: Bitmap Asset Inventory

Дата: 2026-08-23
Ветка: `codex/kwork-portfolio-pack`
Режим: `CLOUD_ONLY`
Commit: `feat: add portfolio bitmap asset inventory`
Push: не выполнялся по прямому указанию пользователя.

## Результат

Создан `portfolio/kwork_pack/assets.py` с тремя публичными функциями:

- `asset_path()` формирует канонический путь `assets/<slug>/<asset-key>.png`;
- `resolve_project_assets()` требует обычный файл и только после проверки возвращает абсолютный URI через `Path.resolve().as_uri()`;
- `missing_assets()` возвращает упорядоченный tuple всех отсутствующих или не являющихся файлами bitmap-путей.

Fallback на CSS, пустое изображение, stock URL или другой asset отсутствует. Каталог, site renderers, `render.py`, manifest и validation не изменялись в рамках Task 6.

## TDD

RED:

```text
python -m pytest tests/test_portfolio_assets.py -q
ModuleNotFoundError: No module named 'portfolio.kwork_pack.assets'
```

GREEN:

```text
python -m pytest tests/test_portfolio_assets.py -q
4 passed in 0.05s
```

Тесты фиксируют канонический `hero.png`, полный missing inventory, обязательный path-specific `FileNotFoundError` и точный абсолютный `file://` URI.

## Проверка артефактов

Все 15 ожидаемых файлов `artifacts/kwork-portfolio/assets/<slug>/hero.png` прочитаны через Pillow без изменения исходников.

- Количество: 15 present, 0 missing.
- Формат: PNG для каждого файла.
- Размер: `1586x992` для каждого файла.
- Nonblank: максимальное стандартное отклонение RGB превысило `42` для каждого файла при пороге `1.0`.
- URI: каждый project resolver вернул точный `Path.resolve().as_uri()`.
- Prompts: все 15 содержат явное требование `без логотипов и текста`.
- Git: каталог `artifacts/` остается ignored.

## Финальная проверка

```text
focused assets: 4 passed in 0.04s
portfolio tests: 94 passed in 2.46s
full pytest: 466 passed in 11.24s
python -m compileall -q src portfolio tests: exit 0
git diff --check: exit 0
global harness smoke: ok, CLOUD_ONLY, Ollama commands skipped
```

Во время проверки в worktree параллельно появились незавершенные изменения Task 7. После завершения их записи portfolio и full suite были повторены успешно; эти несвязанные файлы не включаются в commit Task 6.
