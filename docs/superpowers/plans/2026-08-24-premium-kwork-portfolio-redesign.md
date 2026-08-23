# Premium Kwork Portfolio Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the deleted template-like pack with 15 independent premium Russian website concepts, five verified desktop screenshots per concept, and publish only the final approved set to Kwork.

**Architecture:** Keep screenshot orchestration and browser chrome shared, but move every website into a dedicated renderer module with its own route map, CSS, content, and semantic bitmap inventory. Add automated uniqueness and visual-density gates, then develop `tochka-hoda` as a flagship quality gate before implementing the other 14 projects.

**Tech Stack:** Python 3.10+, dataclasses, Playwright with installed Chrome, Pillow, HTML/CSS/JavaScript, OpenAI ImageGen, pytest.

**Spec:** `docs/superpowers/specs/2026-08-24-premium-kwork-portfolio-redesign.md`

## Global Constraints

- Exactly 15 projects and exactly five 1920x1280 desktop PNG screenshots per project.
- No mobile shot variants in the new pack.
- Every project owns a dedicated renderer module and at least six unique bitmap assets.
- No photographic bitmap is reused between screenshots or projects.
- The lower 25% of every viewport must contain meaningful rendered content.
- The `tochka-hoda` five-screen flagship must pass automated and manual review before rendering the other projects.
- Existing user-authored Kwork works are never modified or deleted.

---

### Task 1: Replace The Portfolio Contract

**Files:**
- Modify: `portfolio/kwork_pack/models.py`
- Replace: `portfolio/kwork_pack/catalog.py`
- Modify: `tests/test_portfolio_catalog.py`
- Modify: `tests/test_portfolio_manifest.py`

**Interfaces:**
- Produces: `ProjectSpec.renderer_module: str`, `ProjectSpec.shots: tuple[ShotSpec, ...]`, and `ProjectSpec.assets: tuple[AssetSpec, ...]`.
- Produces: five desktop `ShotSpec` values and at least six semantic `AssetSpec` values per project.

- [ ] **Step 1: Write failing catalog tests**

```python
def test_every_project_has_five_desktop_routes_and_dedicated_renderer():
    assert len(PROJECTS) == 15
    assert len({project.renderer_module for project in PROJECTS}) == 15
    for project in PROJECTS:
        assert len(project.shots) == 5
        assert all(shot.layout == "desktop" for shot in project.shots)
        assert len({shot.path for shot in project.shots}) == 5


def test_every_project_declares_a_real_asset_inventory():
    for project in PROJECTS:
        assert len(project.assets) >= 6
        assert len({asset.key for asset in project.assets}) == len(project.assets)
        assert all(asset.filename != "hero.png" for asset in project.assets)
```

- [ ] **Step 2: Run catalog tests and verify RED**

Run: `python -m pytest tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py -q`

Expected: failures for four-shot/mobile catalog and one-asset projects.

- [ ] **Step 3: Implement the new metadata contract**

Add `renderer_module: str` to `ProjectSpec`, replace `cover/content/function/mobile` with five named desktop routes per project, and declare semantic assets such as `workshop_hero`, `diagnostic_closeup`, `mechanic_portrait`, `case_before`, `case_after`, and `service_lounge`.

- [ ] **Step 4: Run catalog tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```powershell
git add portfolio/kwork_pack/models.py portfolio/kwork_pack/catalog.py tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py
git commit -m "refactor: define premium portfolio contract"
git push
```

### Task 2: Add Real Quality And Uniqueness Gates

**Files:**
- Create: `portfolio/kwork_pack/quality.py`
- Modify: `portfolio/kwork_pack/validate.py`
- Create: `tests/test_portfolio_quality.py`
- Modify: `tests/test_portfolio_validation.py`

**Interfaces:**
- Produces: `dhash(path: Path, size: int = 16) -> int`.
- Produces: `hamming_distance(left: int, right: int) -> int`.
- Produces: `bottom_band_metrics(path: Path) -> tuple[float, float]` returning grayscale variance and edge density.
- Produces: `validate_asset_uniqueness(root: Path, projects: Iterable[ProjectSpec]) -> tuple[ValidationIssue, ...]`.

- [ ] **Step 1: Write failing uniqueness and density tests**

```python
def test_duplicate_assets_are_rejected(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (160, 90), "#334455").save(first)
    second.write_bytes(first.read_bytes())
    issues = validate_unique_paths((first, second), min_distance=10)
    assert any(issue.code == "duplicate-asset" for issue in issues)


def test_empty_lower_viewport_is_rejected(tmp_path):
    path = tmp_path / "blank-bottom.png"
    image = Image.new("RGB", (1920, 1280), "white")
    ImageDraw.Draw(image).rectangle((0, 0, 1919, 700), fill="#222222")
    image.save(path)
    variance, edge_density = bottom_band_metrics(path)
    assert variance < 25
    assert edge_density < 0.005
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q`

Expected: import failures for `portfolio.kwork_pack.quality`.

- [ ] **Step 3: Implement deterministic image gates**

Use Pillow grayscale resampling for dHash, SHA-256 for exact duplicates, adjacent-pixel differences for edge density, and `ImageStat.Stat` for lower-band variance. Return diagnostic issues containing both conflicting paths.

- [ ] **Step 4: Integrate gates into `validate_pack`**

Reject exact duplicate assets, near-duplicate assets below the configured Hamming distance, final screenshots with blank lower bands, and cross-project screenshots whose perceptual distance indicates a reused layout.

- [ ] **Step 5: Run tests and verify GREEN**

Run: `python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q`

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```powershell
git add portfolio/kwork_pack/quality.py portfolio/kwork_pack/validate.py tests/test_portfolio_quality.py tests/test_portfolio_validation.py
git commit -m "feat: enforce portfolio visual uniqueness"
git push
```

### Task 3: Introduce Dedicated Site Modules

**Files:**
- Replace: `portfolio/kwork_pack/sites/__init__.py`
- Create: `portfolio/kwork_pack/sites/runtime.py`
- Create: `tests/test_portfolio_site_registry.py`
- Remove after migration: `portfolio/kwork_pack/sites/commercial.py`
- Remove after migration: `portfolio/kwork_pack/sites/leadgen.py`
- Remove after migration: `portfolio/kwork_pack/sites/complex.py`

**Interfaces:**
- Produces: `SiteRenderer = Callable[[ProjectSpec, ShotSpec, Mapping[str, str]], RenderedPage]`.
- Produces: `RenderedPage(html: str, css: str, scripts: str = "")`.
- Produces: `get_renderer(project: ProjectSpec) -> SiteRenderer` importing only `project.renderer_module`.

- [ ] **Step 1: Write a failing registry-isolation test**

```python
def test_each_project_resolves_a_dedicated_renderer_module():
    modules = [get_renderer_module(project) for project in PROJECTS]
    assert len(set(modules)) == 15
    assert all(module.__name__.rsplit(".", 1)[-1] == project.slug.replace("-", "_")
               for module, project in zip(modules, PROJECTS))
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m pytest tests/test_portfolio_site_registry.py -q`

Expected: missing registry/runtime interfaces.

- [ ] **Step 3: Implement the module registry and `RenderedPage`**

Keep only HTML escaping, icons, browser shell, and rendering orchestration shared. Do not expose shared header, hero, card, section, or page-layout helpers.

- [ ] **Step 4: Adapt screenshot rendering to `RenderedPage`**

Update `portfolio/kwork_pack/render.py` so `build_document` receives page-owned CSS and optional script text while retaining local asset staging and exact 1920x1280 screenshots.

- [ ] **Step 5: Run registry and renderer tests**

Run: `python -m pytest tests/test_portfolio_site_registry.py tests/test_portfolio_render.py -q`

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```powershell
git add portfolio/kwork_pack/sites portfolio/kwork_pack/render.py tests/test_portfolio_site_registry.py tests/test_portfolio_render.py
git commit -m "refactor: isolate portfolio site renderers"
git push
```

### Task 4: Build The `tochka-hoda` Flagship

**Files:**
- Create: `portfolio/kwork_pack/sites/tochka_hoda.py`
- Create: `tests/test_portfolio_tochka_hoda.py`
- Generate: `artifacts/kwork-portfolio-v2/assets/tochka-hoda/*.png`
- Generate: `artifacts/kwork-portfolio-v2/tochka-hoda/*.png`

**Interfaces:**
- Produces: `render(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> RenderedPage`.
- Consumes the six-or-more semantic asset keys declared for `tochka-hoda`.

- [ ] **Step 1: Write route, copy, and asset-usage tests**

```python
def test_flagship_routes_render_distinct_real_pages():
    project = project_by_slug("tochka-hoda")
    pages = [render(project, shot, fake_assets(project)) for shot in project.shots]
    assert len({page.html for page in pages}) == 5
    assert all("Точка Хода" in page.html for page in pages)
    assert "41 парамет" in pages[0].html
    assert "BMW X5" in pages[3].html
    assert "Стоимость работ" in pages[4].html


def test_flagship_does_not_reuse_photos_between_routes():
    project = project_by_slug("tochka-hoda")
    pages = [render(project, shot, fake_assets(project)).html for shot in project.shots]
    used = [key for key in asset_keys(project) if sum(key in page for page in pages)]
    assert len(used) == len(set(used))
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_portfolio_tochka_hoda.py -q`

Expected: missing dedicated flagship renderer.

- [ ] **Step 3: Generate and inspect unique flagship photography**

Generate separate text-free 16:9 or 4:3 assets for workshop hero, diagnostic scanner close-up, mechanic portrait, BMW case before, BMW case after, service lounge, and engine inspection. Inspect every file with `view_image` at original detail and regenerate any malformed or generic result.

- [ ] **Step 4: Implement all five flagship routes**

Rebuild the approved red/white visual direction with a dense desktop composition, exact Russian copy, genuine service details, booking controls, case-study evidence, and price filtering. Each route owns its layout and uses a different photo.

- [ ] **Step 5: Render and validate the flagship**

Run: `python -m portfolio.kwork_pack.cli render --output artifacts/kwork-portfolio-v2 --project tochka-hoda`

Run: `python -m portfolio.kwork_pack.cli validate --output artifacts/kwork-portfolio-v2 --project tochka-hoda`

Expected: five valid PNGs and zero issues.

- [ ] **Step 6: Perform original-resolution manual review**

Inspect all five PNGs for content density, typography, realism, crop quality, URL, unique imagery, and visual continuity. Record seven explicit PASS values per screenshot in `artifacts/kwork-portfolio-v2/qa-ledger.md`. Fix and rerender every failed value.

- [ ] **Step 7: Commit**

```powershell
git add portfolio/kwork_pack/sites/tochka_hoda.py tests/test_portfolio_tochka_hoda.py
git commit -m "feat: build premium automotive flagship"
git push
```

### Task 5: Build The Remaining Premium Service Sites

**Files:**
- Create: `portfolio/kwork_pack/sites/dentalea.py`
- Create: `portfolio/kwork_pack/sites/ventkontur.py`
- Create: `portfolio/kwork_pack/sites/syr_hleb.py`
- Create: `portfolio/kwork_pack/sites/kvadrat_remonta.py`
- Create: `tests/test_portfolio_premium_services.py`

**Interfaces:**
- Each module produces the same dedicated `render(...) -> RenderedPage` interface without importing another site module.

- [ ] **Step 1: Write failing project-isolation tests**

Assert five unique routes, distinct root layout markers, domain-specific copy, at least six assets, and no cross-project imports for the four projects.

- [ ] **Step 2: Generate and inspect project-owned photography**

Create and review separate photo sets for dental practice, industrial ventilation, gourmet retail, and residential renovation. No generated file may be copied or referenced by another project.

- [ ] **Step 3: Implement each site one at a time**

Finish, render, validate, and manually review all five screens of one project before starting the next. Use distinct typography, navigation, grid, image treatment, and functional workflows for every module.

- [ ] **Step 4: Run the service-site test group**

Run: `python -m pytest tests/test_portfolio_premium_services.py tests/test_portfolio_quality.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```powershell
git add portfolio/kwork_pack/sites/dentalea.py portfolio/kwork_pack/sites/ventkontur.py portfolio/kwork_pack/sites/syr_hleb.py portfolio/kwork_pack/sites/kvadrat_remonta.py tests/test_portfolio_premium_services.py
git commit -m "feat: add premium service portfolio sites"
git push
```

### Task 6: Build Five Distinct Lead-Generation Sites

**Files:**
- Create: `portfolio/kwork_pack/sites/okna_sfera.py`
- Create: `portfolio/kwork_pack/sites/chistiy_metr.py`
- Create: `portfolio/kwork_pack/sites/teplodom_service.py`
- Create: `portfolio/kwork_pack/sites/berezhny_pereezd.py`
- Create: `portfolio/kwork_pack/sites/pravovaya_opora.py`
- Create: `tests/test_portfolio_leadgen_v2.py`

**Interfaces:**
- Each module produces `render(...) -> RenderedPage` and a distinct conversion workflow suited to its domain.

- [ ] **Step 1: Write failing domain-workflow tests**

Assert measurement configuration, room estimate, fault diagnosis, route calculation, and legal assessment appear only in their matching project.

- [ ] **Step 2: Generate and inspect five independent asset sets**

Produce project-specific real-world photography with no reused subjects, rooms, vehicles, people, or crops.

- [ ] **Step 3: Implement and gate projects sequentially**

For each module: implement five routes, render, run quality validation, inspect five PNGs at original resolution, and record QA before proceeding.

- [ ] **Step 4: Run lead-generation tests**

Run: `python -m pytest tests/test_portfolio_leadgen_v2.py tests/test_portfolio_quality.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```powershell
git add portfolio/kwork_pack/sites/okna_sfera.py portfolio/kwork_pack/sites/chistiy_metr.py portfolio/kwork_pack/sites/teplodom_service.py portfolio/kwork_pack/sites/berezhny_pereezd.py portfolio/kwork_pack/sites/pravovaya_opora.py tests/test_portfolio_leadgen_v2.py
git commit -m "feat: add premium lead generation sites"
git push
```

### Task 7: Build Five Product And Operational Systems

**Files:**
- Create: `portfolio/kwork_pack/sites/severniy_marshrut.py`
- Create: `portfolio/kwork_pack/sites/modulprof.py`
- Create: `portfolio/kwork_pack/sites/doma_u_ozera.py`
- Create: `portfolio/kwork_pack/sites/praktika_navyka.py`
- Create: `portfolio/kwork_pack/sites/gruzcontrol.py`
- Create: `tests/test_portfolio_product_systems_v2.py`

**Interfaces:**
- Each module produces `render(...) -> RenderedPage` with product-appropriate dense interfaces and five coherent states.

- [ ] **Step 1: Write failing workflow and density tests**

Assert ecommerce filtering/cart, modular configuration/comparison, property search/booking, curriculum/lesson workspace, and logistics dispatch/detail flows.

- [ ] **Step 2: Generate and inspect independent bitmap inventories**

Generate product, architecture, hospitality, learning, and logistics photography separately. Operational diagrams and maps stay code-native.

- [ ] **Step 3: Implement and gate each system sequentially**

Use operationally realistic density, data, tables, states, and controls; avoid marketing-style card walls in dashboards.

- [ ] **Step 4: Run product-system tests**

Run: `python -m pytest tests/test_portfolio_product_systems_v2.py tests/test_portfolio_quality.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```powershell
git add portfolio/kwork_pack/sites/severniy_marshrut.py portfolio/kwork_pack/sites/modulprof.py portfolio/kwork_pack/sites/doma_u_ozera.py portfolio/kwork_pack/sites/praktika_navyka.py portfolio/kwork_pack/sites/gruzcontrol.py tests/test_portfolio_product_systems_v2.py
git commit -m "feat: add premium product portfolio systems"
git push
```

### Task 8: Remove The Failed Renderer And Validate All 75 Screens

**Files:**
- Delete: `portfolio/kwork_pack/sites/commercial.py`
- Delete: `portfolio/kwork_pack/sites/leadgen.py`
- Delete: `portfolio/kwork_pack/sites/complex.py`
- Modify: `portfolio/kwork_pack/gallery.py`
- Modify: `portfolio/kwork_pack/manifest.py`
- Modify: `README.md`
- Generate: `artifacts/kwork-portfolio-v2/gallery.html`
- Generate: `artifacts/kwork-portfolio-v2/qa-ledger.md`
- Generate: `artifacts/kwork-portfolio-v2/upload-manifest.json`

**Interfaces:**
- Produces a final manifest containing 15 works and five ordered PNG paths per work.

- [ ] **Step 1: Remove legacy renderer imports and tests**

Delete the three shared site-family modules only after every project resolves its dedicated renderer. Update tests so importing any legacy module fails.

- [ ] **Step 2: Render and validate the full pack**

Run: `python -m portfolio.kwork_pack.cli render --output artifacts/kwork-portfolio-v2`

Run: `python -m portfolio.kwork_pack.cli validate --output artifacts/kwork-portfolio-v2`

Expected: `75 screenshots checked; 0 issues` and no duplicate/near-duplicate findings.

- [ ] **Step 3: Perform the complete manual review**

Open the generated gallery and inspect all 75 original-resolution images. Every ledger row must explicitly pass content, composition, typography, asset quality, realism, URL, and uniqueness.

- [ ] **Step 4: Run all automated checks**

Run: `python -m pytest`

Run: `C:\Users\user\.codex\scripts\harness.cmd smoke`

Expected: all tests and smoke checks pass.

- [ ] **Step 5: Update documentation and commit**

```powershell
git add -A
git commit -m "feat: replace Kwork portfolio with premium sites"
git push
```

### Task 9: Publish The Verified Pack To Kwork

**Files:**
- Read: `artifacts/kwork-portfolio-v2/upload-manifest.json`
- Create: `artifacts/kwork-portfolio-v2/upload-results.json`

**Interfaces:**
- Consumes the final 15-work manifest.
- Produces verified Kwork work IDs and server-side image counts.

- [ ] **Step 1: Confirm the existing user portfolio is unchanged**

Record the IDs and titles already present before upload. Do not edit or delete them.

- [ ] **Step 2: Upload one flagship work and verify it**

Upload the five `tochka-hoda` images in order, save, reopen the work, and confirm title plus image count `5`.

- [ ] **Step 3: Upload the remaining 14 works**

For each manifest row, upload the five ordered images, save, and record the new Kwork ID.

- [ ] **Step 4: Perform server-side verification**

Reopen all 15 new works and assert the correct title plus five images. Confirm that no old failed work ID has reappeared.

- [ ] **Step 5: Save publication evidence**

Write `upload-results.json` with 15 titles, Kwork IDs, `image_count: 5`, verification timestamps in `Europe/Moscow`, and `old_user_works_untouched: true`.
