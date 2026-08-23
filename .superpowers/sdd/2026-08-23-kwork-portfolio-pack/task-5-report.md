# Task 5 Report: Complex Portfolio Renderers

Дата: 2026-08-23
Ветка: `codex/kwork-portfolio-pack`
Режим: `CLOUD_ONLY`
Commit: `feat: add complex portfolio concepts`
Push: не выполнялся по прямому указанию пользователя.

## Результат

Создан `portfolio/kwork_pack/sites/complex.py` с пятью отдельными renderer-функциями и четырьмя вариантами для каждого проекта: `cover`, `content`, `function`, `mobile`.

- `sever-market`: витрина экспедиционного магазина, каталог с фильтрами, корзина из двух товаров с выбором доставки и мобильный маршрутный набор.
- `modulprof`: инженерный конфигуратор, спецификация здания, сравнение трёх комплектаций и мобильная сводка.
- `doma-u-ozera`: поиск дома у озера, страница дома и планов, календарь с выбранными датами и мобильное бронирование.
- `praktika`: учебный dashboard, программа курса, lesson workspace с video-state и выполненным заданием, мобильный урок.
- `gruzcontrol`: оперативный обзор, реестр маршрутов, таблица с выбранной доставкой и detail drawer, мобильная диспетчерская лента.

Экспортированы точные `COMPLEX_STATES`, `COMPLEX_LAYOUTS` и `render_complex(project, shot, assets)`. Все динамические brand, palette, slug, variant и asset URL экранируются на HTML-границах. Изображения используют осмысленные русские `alt`, контейнер `aspect-ratio: 16 / 10` и не имеют абсолютных fixed-height overrides.

Каталог обновлён:

- `sever-market`: бренд «Северный маршрут», домен `severniy-marshrut.ru`;
- `praktika`: домен `praktika-navyka.ru`.

## TDD

Catalog RED:

```text
python -m pytest tests/test_portfolio_catalog.py -q
1 failed, 5 passed
Причина: старые бренд и домены.
```

Catalog GREEN:

```text
python -m pytest tests/test_portfolio_catalog.py -q
6 passed
```

Renderer RED:

```text
python -m pytest tests/test_portfolio_sites.py -k complex -q
ModuleNotFoundError: No module named 'portfolio.kwork_pack.sites.complex'
```

Renderer GREEN после реализации:

```text
python -m pytest tests/test_portfolio_sites.py -k complex -q
23 passed, 35 deselected
```

Browser regression RED/GREEN:

- `praktika/function`: обнаружено `1138px` content height при viewport `1120px`; тест сначала упал, затем подтвердил вложение четырёх lesson items внутрь sidebar. Повторная метрика: `1120/1120px`.
- `doma-u-ozera/content`: обнаружено `1121px` при viewport `1120px`; тест сначала упал, затем закрепил `max-width: 980px` для property image. Повторная метрика: `1120/1120px`, image ratio `1.6`.

Финальный focused GREEN:

```text
python -m pytest tests/test_portfolio_sites.py -k complex -q
25 passed, 35 deselected
```

## Browser QA

In-app Browser проверил все 20 HTML-вариантов на итоговом холсте `1920x1280` с локальным безопасным placeholder asset.

- Все desktop viewport: `1834x1120`, без горизонтального или вертикального overflow после исправлений.
- Все mobile viewport: `430x920`, без overflow.
- Все измеренные image slots: ratio `1.6`.
- DOM содержит meaningful Russian UI copy; framework overlays отсутствуют.
- Console `error`/`warn`: пусто на проверенных страницах.
- В корзине переключение с «Курьером» на «Самовывоз» изменило реальный checked radio-state.
- Визуально проверены корзина, property content и mobile-логистика; перекрытий и обрезки текста не обнаружено.

Bitmap-ассеты не входят в Task 5, поэтому визуальная проверка использовала однотонный локальный placeholder. Итоговое framing реальных изображений будет проверяться на этапе render/export.

## Финальная проверка

```text
portfolio tests: 80 passed in 0.23s
full pytest: 452 passed in 9.68s
python -m compileall -q src portfolio tests: exit 0
git diff --check: exit 0
mojibake scan: no markers found
global harness smoke: ok, CLOUD_ONLY, Ollama commands skipped
```

## Review и область изменений

Выполнен локальный diff-review по требованиям brief. Отдельный read-only review через установленный `codex-cli 0.142.1` не стартовал из-за несовместимости CLI с доступной облачной моделью; процесс завершился до чтения diff и не менял файлы.

В Task 5 commit входят только:

- `portfolio/kwork_pack/sites/complex.py`;
- `portfolio/kwork_pack/catalog.py`;
- `tests/test_portfolio_sites.py`;
- `tests/test_portfolio_catalog.py`;
- `.superpowers/sdd/2026-08-23-kwork-portfolio-pack/task-5-report.md`.

`commercial.py`, `leadgen.py` и `tests/test_portfolio_commercial_sizing.py` не изменялись.
