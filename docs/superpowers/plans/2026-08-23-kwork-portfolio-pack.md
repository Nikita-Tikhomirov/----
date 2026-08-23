# Kwork Portfolio Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, render, validate, and publish 15 distinct Russian-language author-concept portfolio works with four 1920x1280 images per work for the user's Kwork profile.

**Architecture:** A standalone Python package under `portfolio/kwork_pack/` owns structured project metadata, reusable browser/page primitives, three groups of site renderers, Playwright screenshot export, validation, and Kwork upload manifests. Site copy and UI are code-native; generated bitmap assets contain no important text. Heavy generated assets and screenshots stay under ignored `artifacts/kwork-portfolio/`, while source, prompts, tests, and reproducible commands are committed.

**Tech Stack:** Python 3.10+, dataclasses, standard-library HTML/JSON/CSV helpers, Playwright for Python using the installed Chrome channel, Pillow for read-only PNG validation, pytest, HTML/CSS/JavaScript, OpenAI ImageGen for bitmap assets.

**Spec:** `docs/superpowers/specs/2026-08-23-kwork-portfolio-pack-design.md`

## Global Constraints

- Produce exactly 15 separate author concepts and exactly four PNG files per concept.
- Every final image is exactly 1920x1280 pixels and no larger than 10 MB.
- Use Russian code-native UI copy; no rasterized AI-generated interface text.
- Every browser address uses the concept's own meaningful `.ru` domain and semantic path; never show `localhost`, `demo`, or the developer's name.
- Check that a proposed domain does not resolve to an active branded site before final rendering; replace collisions with a new semantic name.
- Do not claim a real client, real testimonials, awards, business results, or third-party endorsements.
- Kwork metadata identifies every work as an author concept.
- Keep palettes, page composition, imagery, and functional states visibly distinct across all 15 works.
- Generated assets and final screenshots live in ignored `artifacts/kwork-portfolio/`; source and prompts live in git.
- Do not publish anything to Kwork until all 60 images pass validation and the user confirms the final publication batch at action time.

---

## File Structure

- `portfolio/__init__.py`: marks the portfolio tooling namespace.
- `portfolio/kwork_pack/__init__.py`: exports the public catalog and rendering interfaces.
- `portfolio/kwork_pack/models.py`: immutable `ProjectSpec`, `ShotSpec`, `AssetSpec`, and validation result types.
- `portfolio/kwork_pack/catalog.py`: the authoritative metadata, domain, URL, palette, Kwork copy, shot list, and asset prompt for all 15 concepts.
- `portfolio/kwork_pack/icons.py`: a small named set of official Lucide SVG path data used by code-native controls.
- `portfolio/kwork_pack/components.py`: escaped HTML primitives for navigation, buttons, forms, product rows, metrics, browser frames, and mobile frames.
- `portfolio/kwork_pack/shell.py`: assembles complete 1920x1280 documents and applies shared browser/mobile chrome.
- `portfolio/kwork_pack/sites/commercial.py`: five commercial-site renderers.
- `portfolio/kwork_pack/sites/leadgen.py`: five lead-generation landing-page renderers.
- `portfolio/kwork_pack/sites/complex.py`: five store, booking, education, and dashboard renderers.
- `portfolio/kwork_pack/assets.py`: expected asset names, local resolution, and generated-asset completeness checks.
- `portfolio/kwork_pack/render.py`: Playwright launch, HTML staging, single-shot and batch PNG rendering.
- `portfolio/kwork_pack/manifest.py`: deterministic JSON/CSV Kwork upload manifests.
- `portfolio/kwork_pack/validate.py`: dimensions, byte size, count, URL/copy marker, and asset validation.
- `portfolio/kwork_pack/gallery.py`: local HTML contact sheets for visual review of every output.
- `portfolio/kwork_pack/domain_check.py`: injectable DNS collision checks for invented portfolio domains.
- `portfolio/kwork_pack/cli.py`: `domains`, `render`, `validate`, `gallery`, and `manifest` commands.
- `portfolio/kwork_pack/static/base.css`: shared typography, reset, browser frame, responsive canvas, and accessibility rules.
- `portfolio/kwork_pack/static/themes.css`: named color/type tokens for all 15 projects.
- `tests/test_portfolio_catalog.py`: catalog, domain, title, shot, and uniqueness contracts.
- `tests/test_portfolio_shell.py`: safe HTML assembly and browser/mobile URL framing.
- `tests/test_portfolio_sites.py`: unique copy, layouts, and functional-state markers for all 15 renderers.
- `tests/test_portfolio_render.py`: one real Chrome screenshot smoke test and deterministic filenames.
- `tests/test_portfolio_manifest.py`: Kwork JSON/CSV output contracts.
- `tests/test_portfolio_validation.py`: missing files, dimensions, size, and complete-pack validation.
- `tests/test_portfolio_domain_check.py`: deterministic resolved/unresolved domain checks without live DNS in unit tests.
- `README.md`: portfolio generation, review, output, and upload instructions.

---

### Task 1: Catalog And Domain Contracts

**Files:**
- Create: `portfolio/__init__.py`
- Create: `portfolio/kwork_pack/__init__.py`
- Create: `portfolio/kwork_pack/models.py`
- Create: `portfolio/kwork_pack/catalog.py`
- Create: `tests/test_portfolio_catalog.py`

**Interfaces:**
- Produces: `ShotSpec(key: str, public_path: str, layout: Literal["desktop", "mobile"], variant: str)`.
- Produces: `AssetSpec(key: str, filename: str, prompt: str)`.
- Produces: `ProjectSpec(slug: str, brand: str, kwork_title: str, group: str, domain: str, category: tuple[str, str], work_type: str, description: str, palette: str, shots: tuple[ShotSpec, ...], assets: tuple[AssetSpec, ...])`.
- Produces: `PROJECTS: tuple[ProjectSpec, ...]`, `get_project(slug: str) -> ProjectSpec`, and `public_url(project: ProjectSpec, shot: ShotSpec) -> str`.

- [ ] **Step 1: Write the failing catalog tests**

```python
from portfolio.kwork_pack.catalog import PROJECTS, get_project, public_url


def test_catalog_contains_fifteen_distinct_projects_and_sixty_shots():
    assert len(PROJECTS) == 15
    assert len({project.slug for project in PROJECTS}) == 15
    assert sum(len(project.shots) for project in PROJECTS) == 60
    assert [shot.key for project in PROJECTS for shot in project.shots] == [
        "cover", "content", "function", "mobile"
    ] * 15


def test_public_urls_are_semantic_and_never_look_like_local_demos():
    for project in PROJECTS:
        assert project.domain.endswith(".ru")
        assert "demo" not in project.domain
        assert "nikita" not in project.domain
        for shot in project.shots:
            url = public_url(project, shot)
            assert url.startswith(f"https://{project.domain}/")
            assert "localhost" not in url


def test_kwork_titles_fit_form_limit_and_identify_author_concepts():
    for project in PROJECTS:
        assert 1 <= len(project.kwork_title) <= 40
        assert "Авторский концепт" in project.description


def test_tochka_hoda_uses_automotive_content_path():
    project = get_project("tochka-hoda")
    assert project.domain == "tochka-hoda.ru"
    assert project.shots[1].public_path == "/uslugi/diagnostika-avtomobilya"
```

- [ ] **Step 2: Run the catalog tests and verify RED**

Run: `python -m pytest tests/test_portfolio_catalog.py -q`

Expected: FAIL because `portfolio.kwork_pack.catalog` does not exist.

- [ ] **Step 3: Implement immutable models and all 15 catalog records**

Use this exact public skeleton in `models.py`:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ShotSpec:
    key: str
    public_path: str
    layout: Literal["desktop", "mobile"]
    variant: str


@dataclass(frozen=True)
class AssetSpec:
    key: str
    filename: str
    prompt: str


@dataclass(frozen=True)
class ProjectSpec:
    slug: str
    brand: str
    kwork_title: str
    group: str
    domain: str
    category: tuple[str, str]
    work_type: str
    description: str
    palette: str
    shots: tuple[ShotSpec, ...]
    assets: tuple[AssetSpec, ...]
```

Create records for these exact slug/domain/title triples:

```python
PROJECT_IDENTITIES = (
    ("tochka-hoda", "tochka-hoda.ru", "Сайт автосервиса «Точка Хода»"),
    ("dentalea", "dentalea-clinic.ru", "Сайт стоматологии «Денталея»"),
    ("ventkontur", "ventkontur.ru", "Каталог вентиляции «ВентКонтур»"),
    ("syr-hleb", "syr-hleb.ru", "Интернет-магазин «Сыр и Хлеб»"),
    ("kvadrat-remonta", "kvadrat-remonta.ru", "Сайт ремонта квартир"),
    ("okna-sfera", "okna-sfera.ru", "Лендинг пластиковых окон"),
    ("chistiy-metr", "chistiy-metr.ru", "Лендинг клининговой компании"),
    ("teplodom", "teplodom-service.ru", "Лендинг ремонта котлов"),
    ("pereezd-prosto", "pereezd-prosto.ru", "Лендинг квартирных переездов"),
    ("pravo-opora", "pravo-opora.ru", "Лендинг юридической компании"),
    ("sever-market", "sever-market.ru", "Магазин туристического снаряжения"),
    ("modulprof", "modulprof.ru", "B2B-каталог модульных зданий"),
    ("doma-u-ozera", "doma-u-ozera.ru", "Сервис бронирования домов"),
    ("praktika", "praktika-online.ru", "Образовательная платформа"),
    ("gruzcontrol", "gruzcontrol.ru", "Кабинет управления доставками"),
)
```

Each project must define four paths from the approved spec, use category `("Разработка и IT", "Создание сайта")`, work type `"Новый сайт"`, and begin its description with `"Авторский концепт"`.

- [ ] **Step 4: Run catalog tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_catalog.py -q`

Expected: all tests PASS.

- [ ] **Step 5: Commit the catalog contract**

```powershell
git add portfolio tests/test_portfolio_catalog.py
git commit -m "feat: define Kwork portfolio catalog"
```

---

### Task 2: Browser Shell And Rendering Primitives

**Files:**
- Create: `portfolio/kwork_pack/icons.py`
- Create: `portfolio/kwork_pack/components.py`
- Create: `portfolio/kwork_pack/shell.py`
- Create: `portfolio/kwork_pack/static/base.css`
- Create: `portfolio/kwork_pack/static/themes.css`
- Create: `tests/test_portfolio_shell.py`

**Interfaces:**
- Consumes: `ProjectSpec`, `ShotSpec`, and `public_url()` from Task 1.
- Produces: `icon(name: str, *, size: int = 20) -> str`.
- Produces: `render_browser_shell(project: ProjectSpec, shot: ShotSpec, page_html: str) -> str`.
- Produces: `render_mobile_shell(project: ProjectSpec, shot: ShotSpec, page_html: str) -> str`.
- Produces: `build_document(project: ProjectSpec, shot: ShotSpec, page_html: str, css_text: str) -> str`.

- [ ] **Step 1: Write failing shell tests**

```python
from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.shell import build_document


def test_desktop_document_contains_realistic_browser_url_and_canvas_contract():
    project = get_project("tochka-hoda")
    shot = project.shots[1]
    html = build_document(project, shot, '<main data-page="diagnostics">Контент</main>', "")
    assert "https://tochka-hoda.ru/uslugi/diagnostika-avtomobilya" in html
    assert 'data-canvas="1920x1280"' in html
    assert "localhost" not in html


def test_mobile_document_uses_mobile_browser_frame_without_changing_output_canvas():
    project = get_project("doma-u-ozera")
    shot = next(item for item in project.shots if item.key == "mobile")
    html = build_document(project, shot, "<main>Дом с сауной</main>", "")
    assert 'data-layout="mobile"' in html
    assert 'data-canvas="1920x1280"' in html
    assert "doma-u-ozera.ru" in html
```

- [ ] **Step 2: Run shell tests and verify RED**

Run: `python -m pytest tests/test_portfolio_shell.py -q`

Expected: FAIL because `portfolio.kwork_pack.shell` does not exist.

- [ ] **Step 3: Implement escaped components and browser/mobile shells**

`build_document()` must HTML-escape all dynamic brand, URL, label, and body values that are not already returned by trusted renderer functions. The desktop shell contains traffic-light window controls, a lock icon from `icons.py`, and a single URL bar. The mobile shell contains a 430x920 phone viewport centered inside the 1920x1280 canvas with the same semantic URL visible.

Use these fixed canvas rules in `base.css`:

```css
html, body { width: 1920px; height: 1280px; margin: 0; overflow: hidden; }
* { box-sizing: border-box; letter-spacing: 0; }
.portfolio-canvas { width: 1920px; height: 1280px; background: #eef1f4; padding: 42px; }
.browser-window { width: 1836px; height: 1196px; border: 1px solid #cbd2d9; border-radius: 8px; overflow: hidden; background: #fff; box-shadow: 0 20px 55px rgba(20, 30, 40, .16); }
.browser-viewport { width: 100%; height: 1120px; overflow: hidden; }
.mobile-device { width: 486px; height: 1080px; margin: 58px auto 0; padding: 28px; border-radius: 54px; background: #17191c; box-shadow: 0 28px 70px rgba(14, 20, 26, .28); }
.mobile-viewport { width: 430px; height: 920px; overflow: hidden; background: #fff; }
```

Use official Lucide path data for `lock`, `arrow-right`, `phone`, `calendar`, `shopping-cart`, `filter`, `check`, and `map-pin`; raise `KeyError` for unknown names.

- [ ] **Step 4: Run shell tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_shell.py -q`

Expected: all tests PASS.

- [ ] **Step 5: Commit shared rendering primitives**

```powershell
git add portfolio/kwork_pack tests/test_portfolio_shell.py
git commit -m "feat: add portfolio browser rendering shell"
```

---

### Task 3: Commercial Site Renderers

**Files:**
- Create: `portfolio/kwork_pack/sites/__init__.py`
- Create: `portfolio/kwork_pack/sites/commercial.py`
- Create: `tests/test_portfolio_sites.py`

**Interfaces:**
- Consumes: `ProjectSpec`, `ShotSpec`, component functions, and asset URLs.
- Produces: `render_commercial(project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]) -> str`.
- Produces site dispatch keys: `tochka-hoda`, `dentalea`, `ventkontur`, `syr-hleb`, `kvadrat-remonta`.

- [ ] **Step 1: Write failing uniqueness and copy tests**

```python
import pytest

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.sites.commercial import render_commercial


@pytest.mark.parametrize(
    ("slug", "required_copy", "functional_marker"),
    [
        ("tochka-hoda", "Диагностика без догадок", 'data-widget="service-booking"'),
        ("dentalea", "План лечения до начала работ", 'data-widget="doctor-schedule"'),
        ("ventkontur", "Подбор по расходу воздуха", 'data-widget="equipment-filter"'),
        ("syr-hleb", "Соберите подарочный набор", 'data-widget="gift-builder"'),
        ("kvadrat-remonta", "Смета по этапам", 'data-widget="estimate-table"'),
    ],
)
def test_commercial_sites_have_unique_value_and_function(slug, required_copy, functional_marker):
    project = get_project(slug)
    html = render_commercial(project, project.shots[2], {"hero": "/asset.webp"})
    assert required_copy in html
    assert functional_marker in html
```

- [ ] **Step 2: Run commercial renderer tests and verify RED**

Run: `python -m pytest tests/test_portfolio_sites.py -k commercial -q`

Expected: FAIL because the commercial renderer does not exist.

- [ ] **Step 3: Implement five genuinely different commercial layouts**

Implement these visible structures without sharing a hero layout:

```python
COMMERCIAL_LAYOUTS = {
    "tochka-hoda": ("split-diagnostic", "service-timeline", "service-booking"),
    "dentalea": ("calm-editorial", "treatment-detail", "doctor-schedule"),
    "ventkontur": ("technical-index", "catalog-table", "equipment-filter"),
    "syr-hleb": ("product-led", "collection-grid", "gift-builder"),
    "kvadrat-remonta": ("project-gallery", "case-study", "estimate-table"),
}
```

Each renderer must provide four variants matching the project's `ShotSpec.variant`, include one stable `data-widget` marker on the functional view, use the project's palette class, and render the relevant image through an `<img>` with fixed `aspect-ratio` and meaningful Russian `alt` text.

- [ ] **Step 4: Run commercial tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_sites.py -k commercial -q`

Expected: all commercial cases PASS.

- [ ] **Step 5: Commit commercial concepts**

```powershell
git add portfolio/kwork_pack/sites/commercial.py tests/test_portfolio_sites.py
git commit -m "feat: add commercial portfolio concepts"
```

---

### Task 4: Lead-Generation Site Renderers

**Files:**
- Create: `portfolio/kwork_pack/sites/leadgen.py`
- Modify: `tests/test_portfolio_sites.py`

**Interfaces:**
- Consumes: the same models and components as Task 3.
- Produces: `render_leadgen(project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]) -> str`.
- Produces site dispatch keys: `okna-sfera`, `chistiy-metr`, `teplodom`, `pereezd-prosto`, `pravo-opora`.

- [ ] **Step 1: Add failing lead-generation tests**

```python
@pytest.mark.parametrize(
    ("slug", "required_copy", "functional_marker"),
    [
        ("okna-sfera", "Рассчитайте окно по вашим размерам", 'data-widget="window-calculator"'),
        ("chistiy-metr", "Квартира готова к заселению", 'data-widget="cleaning-calculator"'),
        ("teplodom", "Вернём тепло в день обращения", 'data-widget="service-request"'),
        ("pereezd-prosto", "Переезд без потерянных коробок", 'data-widget="moving-calculator"'),
        ("pravo-opora", "Оценим перспективу спора", 'data-widget="case-assessment"'),
    ],
)
def test_leadgen_sites_solve_one_clear_customer_problem(slug, required_copy, functional_marker):
    project = get_project(slug)
    html = render_leadgen(project, project.shots[2], {"hero": "/asset.webp"})
    assert required_copy in html
    assert functional_marker in html
```

- [ ] **Step 2: Run lead-generation tests and verify RED**

Run: `python -m pytest tests/test_portfolio_sites.py -k leadgen -q`

Expected: FAIL because `render_leadgen` does not exist.

- [ ] **Step 3: Implement five conversion-focused but visually distinct layouts**

Use these exact functional flows:

```python
LEADGEN_FLOWS = {
    "okna-sfera": ("Размеры", "Профиль", "Монтаж", "Получить расчёт"),
    "chistiy-metr": ("Площадь", "Состояние", "Дополнительные зоны", "Узнать стоимость"),
    "teplodom": ("Марка котла", "Симптом", "Адрес", "Вызвать мастера"),
    "pereezd-prosto": ("Откуда", "Куда", "Объём вещей", "Рассчитать переезд"),
    "pravo-opora": ("Тип договора", "Срок просрочки", "Сумма", "Получить оценку"),
}
```

The forms are presentational and must show completed sample states, clear labels, checkboxes for binary options, numeric inputs for measurable values, and one primary command. Do not invent fake countdown timers, inflated conversion metrics, or guaranteed outcomes.

- [ ] **Step 4: Run lead-generation tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_sites.py -k leadgen -q`

Expected: all lead-generation cases PASS.

- [ ] **Step 5: Commit lead-generation concepts**

```powershell
git add portfolio/kwork_pack/sites/leadgen.py tests/test_portfolio_sites.py
git commit -m "feat: add lead generation portfolio concepts"
```

---

### Task 5: Store, Booking, Education, And Dashboard Renderers

**Files:**
- Create: `portfolio/kwork_pack/sites/complex.py`
- Modify: `tests/test_portfolio_sites.py`

**Interfaces:**
- Consumes: the same models and components as Tasks 3 and 4.
- Produces: `render_complex(project: ProjectSpec, shot: ShotSpec, assets: dict[str, str]) -> str`.
- Produces site dispatch keys: `sever-market`, `modulprof`, `doma-u-ozera`, `praktika`, `gruzcontrol`.

- [ ] **Step 1: Add failing complex-site tests**

```python
@pytest.mark.parametrize(
    ("slug", "required_copy", "functional_marker"),
    [
        ("sever-market", "Снаряжение для маршрута", 'data-widget="shopping-cart"'),
        ("modulprof", "Комплектация без скрытых позиций", 'data-widget="building-comparison"'),
        ("doma-u-ozera", "Выберите свободные даты", 'data-widget="booking-calendar"'),
        ("praktika", "Продолжить обучение", 'data-widget="lesson-workspace"'),
        ("gruzcontrol", "Доставки сегодня", 'data-widget="delivery-table"'),
    ],
)
def test_complex_sites_show_a_real_workflow_state(slug, required_copy, functional_marker):
    project = get_project(slug)
    html = render_complex(project, project.shots[2], {"hero": "/asset.webp"})
    assert required_copy in html
    assert functional_marker in html
```

- [ ] **Step 2: Run complex-site tests and verify RED**

Run: `python -m pytest tests/test_portfolio_sites.py -k complex -q`

Expected: FAIL because `render_complex` does not exist.

- [ ] **Step 3: Implement five domain-specific workflows**

Use these exact functional states:

```python
COMPLEX_STATES = {
    "sever-market": "cart-with-two-products-and-delivery-choice",
    "modulprof": "three-column-building-comparison",
    "doma-u-ozera": "calendar-with-selected-weekend-and-house",
    "praktika": "lesson-video-outline-and-completed-task",
    "gruzcontrol": "delivery-table-with-selected-detail-drawer",
}
```

The operational interfaces must remain quiet and work-focused. Use tables, filters, tabs, rows, and detail panels instead of marketing cards. The consumer store and booking surfaces must prioritize real product/place imagery and preserve a hint of the following section in the first viewport.

- [ ] **Step 4: Run complex-site tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_sites.py -k complex -q`

Expected: all complex-site cases PASS.

- [ ] **Step 5: Commit complex concepts**

```powershell
git add portfolio/kwork_pack/sites/complex.py tests/test_portfolio_sites.py
git commit -m "feat: add complex portfolio concepts"
```

---

### Task 6: Bitmap Asset Inventory And Generation

**Files:**
- Create: `portfolio/kwork_pack/assets.py`
- Create: `tests/test_portfolio_assets.py`
- Generate locally: `artifacts/kwork-portfolio/assets/<slug>/hero.png`

**Interfaces:**
- Consumes: `ProjectSpec.assets` from Task 1.
- Produces: `asset_path(root: Path, project: ProjectSpec, asset: AssetSpec) -> Path`.
- Produces: `resolve_project_assets(root: Path, project: ProjectSpec) -> dict[str, str]` returning file URI strings.
- Produces: `missing_assets(root: Path, projects: Iterable[ProjectSpec]) -> tuple[Path, ...]`.

- [ ] **Step 1: Write failing asset inventory tests**

```python
import pytest

from portfolio.kwork_pack.assets import missing_assets, resolve_project_assets
from portfolio.kwork_pack.catalog import PROJECTS


def test_missing_assets_reports_every_expected_file(tmp_path):
    missing = missing_assets(tmp_path, PROJECTS)
    assert len(missing) == 15
    assert missing[0].name == "hero.png"


def test_resolve_project_assets_requires_generated_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="hero.png"):
        resolve_project_assets(tmp_path, PROJECTS[0])
```

- [ ] **Step 2: Run asset tests and verify RED**

Run: `python -m pytest tests/test_portfolio_assets.py -q`

Expected: FAIL because `portfolio.kwork_pack.assets` does not exist.

- [ ] **Step 3: Implement strict asset resolution**

Never substitute a CSS gradient, empty rectangle, or unrelated stock fallback when a required bitmap is missing. Return `Path.resolve().as_uri()` only after checking `is_file()` and raise a path-specific error otherwise.

- [ ] **Step 4: Run asset tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_assets.py -q`

Expected: all tests PASS.

- [ ] **Step 5: Generate one text-free production asset per concept with ImageGen**

Use each catalog prompt with these shared requirements appended verbatim:

```text
Photorealistic commercial website hero asset, landscape 16:9, natural light,
clear inspectable subject, room for interface copy outside the image crop,
no text, no letters, no logos, no watermarks, no gradients, no stock-photo look.
```

The subject prompts are:

```python
ASSET_SUBJECTS = {
    "tochka-hoda": "Современный чистый российский автосервис, механик проводит компьютерную диагностику обычного семейного автомобиля",
    "dentalea": "Светлый современный стоматологический кабинет, врач спокойно консультирует взрослого пациента, без медицинских процедур крупным планом",
    "ventkontur": "Промышленная вентиляционная установка в чистом техническом помещении, инженер проверяет оборудование",
    "syr-hleb": "Премиальный набор российских сыров, свежего хлеба и ягод на светлом столе, честная предметная съёмка",
    "kvadrat-remonta": "Современная московская квартира после качественного ремонта, видны материалы и аккуратные детали отделки",
    "okna-sfera": "Светлая жилая комната с большим новым окном, естественный дневной свет и городской вид",
    "chistiy-metr": "Профессиональная уборка светлой квартиры после ремонта, специалист с безопасным оборудованием",
    "teplodom": "Мастер обслуживает настенный газовый котёл в аккуратной домашней котельной",
    "pereezd-prosto": "Организованный квартирный переезд, подписанные коробки и сотрудники аккуратно загружают мебель",
    "pravo-opora": "Деловая консультация российского юриста с семейной парой за светлым столом, документы без читаемого текста",
    "sever-market": "Современное туристическое снаряжение для похода разложено у хвойного леса, палатка, рюкзак и фонарь",
    "modulprof": "Современное модульное здание на производственной площадке, чистая архитектурная съёмка",
    "doma-u-ozera": "Современный деревянный дом у спокойного северного озера, ясный день, фасад и территория хорошо видны",
    "praktika": "Рабочее место взрослого онлайн-студента, ноутбук, блокнот и спокойный современный интерьер без читаемого текста на экране",
    "gruzcontrol": "Современный распределительный центр, грузовые автомобили и организованная погрузка, дневной свет",
}
```

Save each returned bitmap as the exact expected `hero.png` path. Inspect every generated asset with `view_image`; regenerate assets with text artifacts, malformed hands, unreadable products, or mismatched subject matter.

- [ ] **Step 6: Verify all 15 assets are present**

Run: `python -m portfolio.kwork_pack.cli validate-assets --output artifacts/kwork-portfolio`

Expected: `15 assets present; 0 missing`.

- [ ] **Step 7: Commit the asset contract and prompts**

```powershell
git add portfolio/kwork_pack/assets.py portfolio/kwork_pack/catalog.py tests/test_portfolio_assets.py
git commit -m "feat: define portfolio image assets"
```

---

### Task 7: Playwright Renderer And Deterministic File Names

**Files:**
- Modify: `pyproject.toml`
- Create: `portfolio/kwork_pack/render.py`
- Create: `tests/test_portfolio_render.py`

**Interfaces:**
- Consumes: catalog projects, site renderers, shell, and resolved assets.
- Produces: `render_shot(project: ProjectSpec, shot: ShotSpec, output_root: Path, *, chrome_channel: str = "chrome") -> Path`.
- Produces: `render_project(project: ProjectSpec, output_root: Path, *, chrome_channel: str = "chrome") -> tuple[Path, ...]`.
- Produces: `render_all(projects: Iterable[ProjectSpec], output_root: Path, *, chrome_channel: str = "chrome") -> tuple[Path, ...]`.

- [ ] **Step 1: Add reproducible portfolio dependencies**

Add this optional group to `pyproject.toml`:

```toml
portfolio = [
    "playwright>=1.55,<2",
    "Pillow>=10,<13",
]
```

- [ ] **Step 2: Write failing renderer tests**

```python
import pytest
from PIL import Image

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.render import output_path, render_shot


@pytest.fixture
def generated_assets(tmp_path):
    asset = tmp_path / "assets" / "tochka-hoda" / "hero.png"
    asset.parent.mkdir(parents=True)
    Image.new("RGB", (1600, 900), "#d7dde2").save(asset)
    return asset


def test_output_path_uses_stable_numbered_names(tmp_path):
    project = get_project("tochka-hoda")
    assert output_path(tmp_path, project, project.shots[0]).name == "01-cover.png"
    assert output_path(tmp_path, project, project.shots[3]).name == "04-mobile.png"


def test_real_chrome_render_is_exactly_1920_by_1280(tmp_path, generated_assets):
    project = get_project("tochka-hoda")
    path = render_shot(project, project.shots[0], tmp_path)
    with Image.open(path) as image:
        assert image.size == (1920, 1280)
```

The `generated_assets` fixture creates a valid local test PNG in the expected temporary asset path; it never uses a network URL.

- [ ] **Step 3: Run renderer tests and verify RED**

Run: `python -m pytest tests/test_portfolio_render.py -q`

Expected: FAIL because `portfolio.kwork_pack.render` does not exist.

- [ ] **Step 4: Implement headless installed-Chrome rendering**

Use Playwright's synchronous API with `chromium.launch(channel="chrome", headless=True)`, a context viewport of 1920x1280, device scale factor 1, reduced motion, and `page.set_content(..., wait_until="load")`. Wait for `document.fonts.ready` and for every image to report `complete && naturalWidth > 0`; time out with the project slug and shot key in the error. Capture `page.screenshot(path=..., full_page=False)` and close browser resources in `finally` blocks.

- [ ] **Step 5: Run renderer tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_render.py -q`

Expected: all tests PASS and one 1920x1280 PNG is written under pytest's temporary directory.

- [ ] **Step 6: Commit the renderer**

```powershell
git add pyproject.toml portfolio/kwork_pack/render.py tests/test_portfolio_render.py
git commit -m "feat: render portfolio images with Chrome"
```

---

### Task 8: Manifest, Pack Validation, Gallery, And CLI

**Files:**
- Create: `portfolio/kwork_pack/manifest.py`
- Create: `portfolio/kwork_pack/validate.py`
- Create: `portfolio/kwork_pack/gallery.py`
- Create: `portfolio/kwork_pack/domain_check.py`
- Create: `portfolio/kwork_pack/cli.py`
- Create: `tests/test_portfolio_manifest.py`
- Create: `tests/test_portfolio_validation.py`
- Create: `tests/test_portfolio_domain_check.py`

**Interfaces:**
- Consumes: all catalog and renderer outputs.
- Produces: `write_manifests(projects: Iterable[ProjectSpec], output_root: Path) -> tuple[Path, Path]`.
- Produces: `ValidationIssue(project_slug: str, file: str, message: str)` and `ValidationReport(files_checked: int, issues: tuple[ValidationIssue, ...])`.
- Produces: `validate_pack(projects: Iterable[ProjectSpec], output_root: Path) -> ValidationReport`.
- Produces: `write_gallery(projects: Iterable[ProjectSpec], output_root: Path) -> Path`.
- Produces: `DomainStatus(domain: str, resolves: bool, addresses: tuple[str, ...])` and `check_domain(domain: str, resolver: Callable = socket.getaddrinfo) -> DomainStatus`.
- Produces CLI commands `domains`, `validate-assets`, `render`, `manifest`, `validate`, and `gallery`.

- [ ] **Step 1: Write failing manifest tests**

```python
import csv
import json

from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.manifest import write_manifests


def test_manifests_contain_fifteen_upload_rows_and_four_ordered_images(tmp_path):
    json_path, csv_path = write_manifests(PROJECTS, tmp_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload["works"]) == 15
    assert payload["works"][0]["images"] == [
        "tochka-hoda/01-cover.png",
        "tochka-hoda/02-content.png",
        "tochka-hoda/03-function.png",
        "tochka-hoda/04-mobile.png",
    ]
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 15
```

- [ ] **Step 2: Write failing validation tests**

```python
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.validate import validate_pack


def test_empty_pack_reports_all_sixty_missing_images(tmp_path):
    report = validate_pack(PROJECTS, tmp_path)
    assert report.files_checked == 0
    assert len(report.issues) == 60
    assert all(issue.message == "missing image" for issue in report.issues)


def test_complete_pack_rejects_wrong_dimensions(tmp_path, complete_fake_pack):
    complete_fake_pack(size=(1600, 900))
    report = validate_pack(PROJECTS, tmp_path)
    assert any("expected 1920x1280" in issue.message for issue in report.issues)
```

- [ ] **Step 3: Write failing domain-collision tests**

```python
import socket

from portfolio.kwork_pack.domain_check import check_domain


def test_resolved_domain_is_treated_as_a_collision():
    def resolver(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.10", 0))]

    status = check_domain("tochka-hoda.ru", resolver=resolver)
    assert status.resolves is True
    assert status.addresses == ("203.0.113.10",)


def test_unresolved_domain_is_available_for_a_concept():
    def resolver(*_args, **_kwargs):
        raise socket.gaierror("not found")

    status = check_domain("tochka-hoda.ru", resolver=resolver)
    assert status.resolves is False
    assert status.addresses == ()
```

- [ ] **Step 4: Run manifest, validation, and domain tests and verify RED**

Run: `python -m pytest tests/test_portfolio_manifest.py tests/test_portfolio_validation.py tests/test_portfolio_domain_check.py -q`

Expected: FAIL because the modules do not exist.

- [ ] **Step 5: Implement UTF-8 manifests, strict validation, and injectable domain checks**

The JSON manifest uses `ensure_ascii=False` and two-space indentation. The CSV uses `utf-8-sig` so Excel shows Russian text correctly. Validation checks exactly four expected files per project, PNG format, 1920x1280 dimensions, byte size <= 10_000_000, and zero unexpected PNG files in each project directory.

The gallery is a local HTML page with 15 unframed project sections and four fixed-aspect thumbnails per section. It displays title, domain, Kwork description, and validation state; it never rewrites output images.

`check_domain()` deduplicates IPv4/IPv6 addresses returned by the resolver. Any successfully resolved address is a collision and blocks final rendering until the catalog is renamed. `socket.gaierror` produces an unresolved status; other resolver errors are surfaced instead of being treated as availability.

- [ ] **Step 6: Implement the CLI dispatch**

Use this command contract:

```text
python -m portfolio.kwork_pack.cli domains --check
python -m portfolio.kwork_pack.cli validate-assets --output artifacts/kwork-portfolio
python -m portfolio.kwork_pack.cli render --output artifacts/kwork-portfolio
python -m portfolio.kwork_pack.cli manifest --output artifacts/kwork-portfolio
python -m portfolio.kwork_pack.cli validate --output artifacts/kwork-portfolio
python -m portfolio.kwork_pack.cli gallery --output artifacts/kwork-portfolio
```

Every command exits 0 on success and nonzero with readable per-project diagnostics on failure.

- [ ] **Step 7: Run manifest, validation, and domain tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_manifest.py tests/test_portfolio_validation.py tests/test_portfolio_domain_check.py -q`

Expected: all tests PASS.

- [ ] **Step 8: Run the full project test suite**

Run: `python -m pytest -q`

Expected: all existing lead-funnel and new portfolio tests PASS.

- [ ] **Step 9: Commit manifests, validation, gallery, domain checks, and CLI**

```powershell
git add portfolio/kwork_pack tests/test_portfolio_manifest.py tests/test_portfolio_validation.py tests/test_portfolio_domain_check.py
git commit -m "feat: validate and package Kwork portfolio"
```

---

### Task 9: Render All 60 Images And Perform Visual QA

**Files:**
- Generate locally: `artifacts/kwork-portfolio/<slug>/*.png`
- Generate locally: `artifacts/kwork-portfolio/upload-manifest.json`
- Generate locally: `artifacts/kwork-portfolio/upload-manifest.csv`
- Generate locally: `artifacts/kwork-portfolio/gallery.html`
- Modify as defects require: `portfolio/kwork_pack/sites/*.py`, `portfolio/kwork_pack/static/*.css`

**Interfaces:**
- Consumes: the complete generator and all 15 assets.
- Produces: 60 validated final PNG files and a visual QA ledger.

- [ ] **Step 1: Check invented domains for active-site collisions**

Run: `python -m portfolio.kwork_pack.cli domains --check`

Expected: all 15 names report `unresolved/no active branded site`. If a domain resolves, replace that project's brand/domain in the catalog and its tests with a new semantic name before rendering; do not use the active domain.

- [ ] **Step 2: Render the full pack**

Run: `python -m portfolio.kwork_pack.cli render --output artifacts/kwork-portfolio`

Expected: `Rendered 60/60 images` with no missing image, font, or Chrome errors.

- [ ] **Step 3: Generate metadata and gallery**

Run: `python -m portfolio.kwork_pack.cli manifest --output artifacts/kwork-portfolio`

Run: `python -m portfolio.kwork_pack.cli gallery --output artifacts/kwork-portfolio`

Expected: JSON, CSV, and gallery files are written and contain 15 works.

- [ ] **Step 4: Run automated pack validation**

Run: `python -m portfolio.kwork_pack.cli validate --output artifacts/kwork-portfolio`

Expected: `60 files checked; 0 issues`.

- [ ] **Step 5: Inspect all outputs through the gallery and native PNGs**

Open `gallery.html` with the Browser plugin. Inspect all four frames in every project section. For each project, use `view_image` on at least the cover and functional PNG at original detail; inspect mobile PNGs for projects 1, 6, 11, 13, and 15. Record copy, layout, typography, palette, asset crop, domain/URL, and mobile fit in `artifacts/kwork-portfolio/qa-ledger.md`.

- [ ] **Step 6: Fix every material visual defect and re-render affected projects**

For each defect, add or update a focused regression test when the issue is code-detectable, apply the smallest source fix, rerun the focused test, rerender the affected slug, and rerun full pack validation. Material defects include clipped text, overlap, template-like repetition, weak image crop, wrong domain/path, browser-default typography, unreadable controls, missing next-section hint, and mobile overflow.

- [ ] **Step 7: Run final verification and commit source corrections**

Run: `python -m pytest -q`

Run: `python -m compileall -q src portfolio tests`

Run: `git diff --check`

Run: `C:\Users\user\.codex\scripts\harness.cmd smoke`

Expected: all tests pass, compilation and diff checks exit 0, harness reports `ok: true` in `CLOUD_ONLY` mode.

```powershell
git add portfolio tests pyproject.toml
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -m "feat: complete Kwork portfolio pack" }
git push
```

---

### Task 10: Documentation And Kwork Publication

**Files:**
- Modify: `README.md`
- Read locally: `artifacts/kwork-portfolio/upload-manifest.json`
- Record locally: `artifacts/kwork-portfolio/upload-results.json`

**Interfaces:**
- Consumes: validated images and manifest from Task 9.
- Produces: reproducible local instructions and 15 published Kwork portfolio cards after user confirmation.

- [ ] **Step 1: Document generation and recovery commands**

Add a `Портфолио Kwork` README section with the six CLI commands from Task 8, the output path, the requirement to inspect `gallery.html`, and the rule that generation never publishes to Kwork.

- [ ] **Step 2: Commit and publish the documentation**

```powershell
git add README.md
git commit -m "docs: explain Kwork portfolio workflow"
git push
```

- [ ] **Step 3: Run a publication preflight**

Confirm `validate` reports zero issues, every Kwork title is <= 40 characters, each project has four readable files <= 10 MB, the existing logged-in Kwork profile is visible, and no publication modal is already holding unsaved unrelated user content.

- [ ] **Step 4: Prepare the first Kwork work without publishing**

Using the existing authorized browser session, open the portfolio form, populate the first manifest row, select `Разработка и IT` / `Создание сайта`, choose `Новый сайт`, and attach the four ordered images. Stop before the final add/publish action and visually verify title, category, type, image order, and concept description.

- [ ] **Step 5: Request action-time confirmation for the 15-work publication batch**

Show the user the first prepared form and a concise list of all 15 titles. Ask for confirmation immediately before any final publication click. Do not interpret prior design approval as publication confirmation.

- [ ] **Step 6: Publish all 15 works and verify each profile card**

After confirmation, publish one work at a time. After each publication, verify that the profile shows the expected title and cover, then record `{slug, title, status, published_at, profile_url}` in `upload-results.json`. On an upload or validation error, stop that work, preserve the remaining local files, record the exact error, and continue only when the state is known and no duplicate card can be created.

- [ ] **Step 7: Final end-to-end report**

Report the number of published works, any drafts or failures, the local artifact directory, test count, final commit, and push status. Do not claim publication for a card unless it is visible in the Kwork profile.
