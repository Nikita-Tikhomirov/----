# Task 7: Sever Market Report

## Scope

Implemented only the `sever-market` product system in
`portfolio/kwork_pack/sites/sever_market.py`. Tests, catalog metadata, shared
production modules, generated portfolio artifacts, and bitmap sources were not
modified.

The renderer exposes `render(project, shot, assets) -> RenderedPage` for all
five catalog routes:

| Route | Product surface | Owned bitmap sources |
| --- | --- | --- |
| `cover` | Seasonal expedition kit and live price/stock | `mountain_tent` |
| `catalog` | Filter rail, dense product matrix, city stock | `hiking_backpack` |
| `tents` | Capacity/weather controls, comparison, selected specification | `gear_closeup` |
| `cart` | Quantity, reservation, promo, delivery mode, reconciled totals | `campfire_scene` |
| `delivery` | City/carrier/pickup controls, route state, coverage matrix | `guide_portrait`, `winter_route` |

Each route resolves only its allowlisted assets. The focused ownership contract
confirmed that every declared bitmap URL occurs exactly once on its assigned
route and nowhere else in the five-page system.

## TDD Evidence

The required RED run was performed before the renderer existed:

```text
python -m pytest -q tests/test_portfolio_product_systems_v2.py -k sever_market
# 1 failed, 24 deselected
# ModuleNotFoundError: No module named 'portfolio.kwork_pack.sites.sever_market'
```

After implementation, the same command passed:

```text
python -m pytest -q tests/test_portfolio_product_systems_v2.py -k sever_market
# 1 passed, 24 deselected
```

The first GREEN attempt exposed a duplicate `[data-cart-count]` marker on the
tents route. The route-local duplicate was removed so the shared retail-header
counter is the single cart state target; the focused workflow then passed.

## Interaction Contract

- Cover season controls update kit name, item list, duration, temperature,
  weight, price, and stock. Winter resolves to `Зимний маршрут`, `48 700 ₽`,
  and `6 комплектов в наличии` without geometry change.
- Catalog winter filtering updates count to `38 товаров`, changes the summary
  to `Подбор для зимнего похода`, and updates city/featured stock facts.
- Tent capacity updates the selected model, capacity, comparison result, price,
  and table fact. Add-to-cart updates the single header cart counter to `1`.
- Cart quantity and delivery mode recompute line total, subtotal, discount,
  delivery, and total. Quantity `2` plus courier reconciles to `35 980 ₽`,
  `−1 500 ₽`, `1 300 ₽`, and `35 780 ₽`.
- Delivery city and carrier controls update summary, hub, transfer, destination,
  arrival, and route note. Kazan express resolves to `29 августа` and `1 490 ₽`.

All selectable buttons use `aria-pressed`; filters use checkboxes; quantity is
a numeric input; city, pickup, and sorting controls are native selects.

## Visual System

The approved concept and the latest five 1920 x 1280 Chrome screenshots were
inspected at original resolution. The implementation keeps the concept's
angular mountain signal, two-line wordmark, serious retail utility, compact
catalog typography, and pine/red/white identity while replacing the old
marketplace-card anatomy with an independent expedition retail system.

Visual comparison ledger:

| Check | Reference evidence | Render evidence | Result |
| --- | --- | --- | --- |
| Brand | Angular mountain mark and two-line wordmark | Code-native angular mark and `СЕВЕРНЫЙ МАРШРУТ` in the first header row | Pass |
| Retail utility | Catalog, search, city and cart are immediate | All four are persistent in the 88px shop bar | Pass |
| Container model | Dense category/filter and stock information | Open filter rail, ruled matrices, cart ledger, route board and coverage table | Pass |
| Palette | Dark outdoor header, white catalog, red actions | Exact pine `#173F32`, white, signal red `#E83B3B`, trail gray and amber rating | Pass |
| Bitmap treatment | Outdoor equipment and route photography | Every assigned source is uncropped enough to identify its real subject and has no text tint | Pass |
| Lower viewport | Assortment continues below the main catalog | Every route ends in a 342px route-specific meaningful band | Pass |
| Typography | Compact Russian retail hierarchy | UI/data remain at 12px or above; prices, stock and headings are tabular and legible | Pass |
| CTA contrast | White utility/action text | Final CSS specificity check leaves white text/icons on pine and red actions | Pass |

No decorative effects, translucent image treatments, curved containers,
floating marketing panels, nested card layouts, duplicate product photography,
or legacy renderer imports are present. Search of the renderer found none of
the forbidden source strings from the product-system tests.

## Geometry And Chrome QA

The Codex Chrome browser binding was unavailable because the browser extension
was not connected. The repository's Playwright Chrome path was therefore used;
it launches with `playwright.chromium.launch(channel="chrome", headless=True)`.

A temporary smoke script outside the repository loaded all five complete HTML
documents, exercised the required interaction on each route, collected browser
console/page errors, and measured the rendered DOM:

```text
cover:    width=1920 height=1120 scrollWidth=1920 scrollHeight=1120 lower=342
catalog:  width=1920 height=1120 scrollWidth=1920 scrollHeight=1120 lower=342
tents:    width=1920 height=1120 scrollWidth=1920 scrollHeight=1120 lower=342
cart:     width=1920 height=1120 scrollWidth=1920 scrollHeight=1120 lower=342
delivery: width=1920 height=1120 scrollWidth=1920 scrollHeight=1120 lower=342
console: clean
```

The lower band begins 778px below the application root and ends exactly at its
bottom. The root remains the test-required 1920px wide while the internal
header and route surface fit the shared browser viewport, preventing the
right-edge clipping found during the first screenshot review.

Five final screenshots were rendered to a temporary directory outside the
repository using the existing project assets. They were inspected for blank
content, missing images, clipping, overlap, horizontal spill, control contrast,
route identity, and lower-band completion. Temporary QA files were removed
after verification.

## Verification

```text
python -m py_compile portfolio/kwork_pack/sites/sever_market.py
# exit 0

python -m pytest -q tests/test_portfolio_product_systems_v2.py -k sever_market
# 1 passed, 24 deselected

Focused parameterized sever-market contracts
# dedicated routes: 1 passed
# exact bitmap ownership: 1 passed
# independence and banned patterns: 1 passed
# canvas and lower quarter: 1 passed

python -m pytest -q tests/test_portfolio_quality.py
# 9 passed

git diff --check
# exit 0

C:\Users\user\.codex\scripts\harness.cmd smoke
# ok: true; mode: CLOUD_ONLY; Ollama commands skipped
```

## Issues

- The Codex Chrome extension was unavailable. Project-owned Playwright Chrome
  rendering and interaction checks completed successfully instead.
- No production issue or unverified sever-market requirement remains.

## Changed Files

- `portfolio/kwork_pack/sites/sever_market.py`
- `.superpowers/sdd/2026-08-24-premium-kwork-portfolio-redesign/task-7-sever-market-report.md`
