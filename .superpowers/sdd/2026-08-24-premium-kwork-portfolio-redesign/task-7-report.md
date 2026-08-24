# Task 7: Sever Market - Fix Round 1

Дата: 2026-08-24

## Статус

Все замечания из `task-7-sever-market-review.md` устранены в dedicated renderer Sever Market. Изменения ограничены renderer, Playwright-тестами Sever Market и этим отчётом.

## TDD evidence

- RED: `python -m pytest -q tests/test_portfolio_product_systems_v2.py -k sever_market -x`
  - результат до реализации: `1 failed, 1 passed, 24 deselected`;
  - первое ожидаемое падение: отсутствовал интерактивный контракт `[data-add-kit]`.
- GREEN: `python -m pytest -q tests/test_portfolio_product_systems_v2.py -k sever_market`
  - результат: `6 passed, 24 deselected`.
- Общие параметризованные контракты Sever Market запущены отдельными node id.
  - результат: `4 passed`.

## Исправления

- Корзина визуально нормализует количество в диапазон 1-4; суммы согласованы для `0`, `5`, курьера, валидного `SEVER1500` и невалидного промокода.
- Вместимость палатки выбирает соответствующую строку сравнения и синхронно обновляет модель, вместимость, цену и состояние добавления в корзину.
- Все перечисленные route-local контролы получили зависимое видимое состояние: готовый комплект, восемь фильтров каталога, сортировка, сброс, наличие, отправка эксперту, погодные параметры, совместимость, промокод, футпринт, оформление, ПВЗ и подтверждение доставки.
- Сезонные фильтры каталога взаимоисключающие; зимний выбор снимает лето и межсезонье.
- Сетка shopbar перераспределена; навигация помещается до корзины без внутреннего overflow и пересечения.
- Playwright-покрытие расширено на все бывшие no-op контролы, крайние значения корзины и геометрию шапки на всех пяти маршрутах.

## Проверки

- `python -m pytest -q tests/test_portfolio_quality.py`: `9 passed`.
- `python -m portfolio.kwork_pack.cli validate --output artifacts/kwork-portfolio-v2 --project sever-market`: `5 файлов, 0 замечаний`.
- Свежий render во временный каталог: `5 из 5` изображений.
- Validator свежего render: `5 файлов, 0 замечаний`.
- Chrome smoke: Playwright Chromium `151.0.7922.170`, все interaction и geometry assertions прошли.
- Визуальный QA: все пять PNG проверены в исходном разрешении; overlap, clipping и потеря нижнего meaningful band не обнаружены.
- `C:\Users\user\.codex\scripts\harness.cmd smoke`: успешно, режим `CLOUD_ONLY`.

## Ограничения и проблемы

Проблем не осталось. Исходные `artifacts/assets` не изменялись; визуальный QA выполнен во временном каталоге.
