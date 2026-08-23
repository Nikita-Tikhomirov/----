# Task 7 Report: Playwright Portfolio Renderer

Дата: 2026-08-23
Ветка: `codex/kwork-portfolio-pack`
Режим: `CLOUD_ONLY`
Commit: `feat: add Playwright portfolio renderer`
Push: не выполнялся по прямому указанию пользователя.

## Результат

Создан `portfolio/kwork_pack/render.py` с публичными функциями:

- `output_path()` формирует стабильные имена `01-cover.png` ... `04-mobile.png`;
- `render_shot()` рендерит один объявленный shot;
- `render_project()` рендерит четыре shot одного проекта;
- `render_all()` сохраняет порядок проектов и shot, используя один Chrome browser/context.

Renderer запускает установленный Chrome через synchronous Playwright с viewport `1920x1280`, `device_scale_factor=1`, reduced motion, светлой схемой, фиксированными locale/timezone и отключёнными screenshot animations. Перед screenshot он ждёт `document.fonts.ready` и успешную загрузку каждого изображения. Page, context и browser закрываются в `finally`.

В `sites/__init__.py` добавлен минимальный dispatcher для трёх существующих групп site renderer. В `pyproject.toml` добавлена optional dependency group `portfolio` с Playwright и Pillow.

Task 7 не реализует asset inventory. В renderer используется узкий injectable `asset_resolver(root, project)`, совместимый с интерфейсом Task 6; default resolver импортируется лениво. Принимаются только существующие локальные `file://` URI, а ошибки содержат project/key и конкретный путь.

## TDD

RED 1, stable paths:

```text
python -m pytest tests/test_portfolio_render.py -q
ModuleNotFoundError: No module named 'portfolio.kwork_pack.render'
```

GREEN 1: `2 passed`.

RED 2, project rendering:

```text
ImportError: cannot import name 'render_project'
```

GREEN 2: `5 passed`.

RED 3, single/batch APIs and diagnostics:

```text
ImportError: cannot import name 'render_all'
```

Real Chrome then exposed a failing local-image integration test: a `file://` image inside a `set_content` document completed with `naturalWidth=0`. A minimal Playwright probe confirmed the failed request; the same verified local bytes loaded successfully as a PNG data URI. The renderer now validates the planned `file://` input path and embeds those local bytes deterministically for the in-memory document.

Final focused GREEN:

```text
python -m pytest tests/test_portfolio_render.py -q
10 passed in 2.45s
```

## Real Chrome Smoke

Environment:

- Chrome `151.0.7922.170`;
- Playwright `1.60.0`;
- Pillow `11.1.0`.

`render_project()` created four real PNG files under ignored `artifacts/kwork-portfolio/tochka-hoda/`:

| File | Dimensions | Bytes | Max RGB stddev | Nonblank |
| --- | --- | ---: | ---: | --- |
| `01-cover.png` | `1920x1280` | 727060 | 75.747 | yes |
| `02-content.png` | `1920x1280` | 134328 | 26.958 | yes |
| `03-function.png` | `1920x1280` | 278057 | 38.062 | yes |
| `04-mobile.png` | `1920x1280` | 174810 | 53.571 | yes |

Cover и mobile PNG дополнительно просмотрены в original detail. Browser chrome показывает `https://tochka-hoda.ru/`, mobile chrome показывает `https://tochka-hoda.ru/uslugi/diagnostika-avtomobilya`; локальный hero asset загружен в обоих кадрах.

## Финальная проверка

```text
full pytest: 466 passed in 11.72s
python -m compileall -q src portfolio tests: exit 0
global harness smoke: ok, CLOUD_ONLY, Ollama commands skipped
```

В commit входят только Task 7 renderer, его tests/dependencies, минимальный site dispatch и этот отчёт. Manifest, validation, gallery и CLI не изменялись. Task 6 появился в worktree параллельно и был сохранён отдельным commit; его файлы не входят в Task 7 commit.
