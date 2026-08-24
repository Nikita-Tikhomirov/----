# Task 7B: Independent Modulprof review

## Scope

- Reviewed only `60df87d..bd7c9b8` (`bd7c9b8 feat: build modulprof portfolio system`).
- Changed files in scope: `portfolio/kwork_pack/sites/modulprof.py` and the Modulprof additions in `tests/test_portfolio_product_systems_v2.py`.
- Requirements, implementer report, complete diff package, and binding inventory were read before review.
- Production code, tests, rendered PNGs, and other artifacts were not modified.

## Verdicts

- **SPEC COMPLIANCE: FAIL**
- **TASK QUALITY: FAIL**
- **OVERALL: CHANGES REQUIRED**

The renderer is visually strong and most interaction math is sound, but two core filtered-result workflows do not reconcile their visible rows, and required interface text is rendered below the 12px floor. The passing tests do not cover those contracts.

## Findings

### P1 - Catalog filters leave an unrelated, invariant result ledger

The catalog renders five hard-coded rows at `portfolio/kwork_pack/sites/modulprof.py:149`, while the filter update at `portfolio/kwork_pack/sites/modulprof.py:445` changes only count, summary, selected detail, delivery, and geography. It never filters or replaces `.mp-building-rows`.

In Chrome, all 27 purpose/area/readiness combinations produced exactly one row set. For `logistics + large + turnkey`, the interface reported `2 решения` and selected `MP-L240`, but still showed five rows: two offices at 72/96 m², a 180 m² warehouse, and the two logistics rows. This violates the required purpose/area/readiness workflow and the binding catalog anatomy requiring filters, compact building rows, and selected model facts to agree.

The added tests assert headline facts at `tests/test_portfolio_product_systems_v2.py:551` and only check distinct summaries/delivery at `tests/test_portfolio_product_systems_v2.py:708`; no assertion inspects filtered catalog rows.

### P1 - Project counts and selected facts do not reconcile with the ledger

The project ledger defines only seven industrial rows at `portfolio/kwork_pack/sites/modulprof.py:283`, but the script reports industrial totals of 12/5/4/3 at `portfolio/kwork_pack/sites/modulprof.py:572`. Chrome reproduced every mismatch:

| Filter | Reported | Visible rows |
| --- | ---: | ---: |
| Industry / all | 12 | 7 |
| Industry / central | 5 | 3 |
| Industry / volga | 4 | 2 |
| Industry / north | 3 | 2 |

There is also a row/detail disagreement for `social + volga`: the only visible row is `Амбулатория · Ульяновск` from `portfolio/kwork_pack/sites/modulprof.py:303`, while the selected result is `ФАП · Ульяновск` from `portfolio/kwork_pack/sites/modulprof.py:593`.

The tests validate one matching social/north state and fingerprint summary facts at `tests/test_portfolio_product_systems_v2.py:612` and `tests/test_portfolio_product_systems_v2.py:734`, but do not reconcile every reported count or selected project against visible rows.

### P2 - Required interface text falls below 12px

The brief requires important text to be at least 12px, and the binding inventory specifies readable 12-14px tables. The renderer sets control labels to 11px at `portfolio/kwork_pack/sites/modulprof.py:377`, catalog result labels to 10px at `portfolio/kwork_pack/sites/modulprof.py:378`, specification headers to 10px at `portfolio/kwork_pack/sites/modulprof.py:385`, and project ledger headers/statuses to 10/11px at `portfolio/kwork_pack/sites/modulprof.py:391`.

Computed-style inspection in Chrome found visible sub-12px text on every route, including filter labels, configurator field labels, result labels, and project/specification table headers. These are operational labels rather than decorative microcopy, so the explicit readability floor is not met.

### P2 - Invalid dimension input is silently calculated as a different building

The visible length/width fields accept keyboard values while declaring limits at `portfolio/kwork_pack/sites/modulprof.py:200`. The calculation silently clamps through `numeric(...)` at `portfolio/kwork_pack/sites/modulprof.py:484` without normalizing the field or showing validation feedback.

In Chrome, visible values `31 × 13` remained in the inputs while the two-floor summary calculated `720 м²` (the clamped `30 × 12 × 2` result). Visible values `5 × 5` calculated `72 м²` (clamped `6 × 6 × 2`), and blank non-required fields also calculated from 6 × 6. Thus the displayed dimensions can disagree with the result state outside the happy path.

### P3

No additional P3 findings.

## Browser Evidence

- Environment: installed Google Chrome `151.0.0.0`, launched with Playwright `channel="chrome"`, viewport 1920 × 1280.
- Exercised all header navigation and primary links on all five routes: 28/28 reached the expected route.
- Cover: all 9 purpose/area combinations exercised; dependent model, dimensions, price, term, mass, and installation state changed with stable geometry.
- Catalog: all 27 purpose/area/readiness combinations exercised; headline/detail facts changed, but the row set remained invariant as described above.
- Configurator: 2,592 combinations across every purpose, three valid lengths, three valid widths, both floors, both shells, all eight engineering-option masks, and all delivery modes. All valid totals equaled the sum of eight parts and the ledger total; zero reconciliation failures; geometry stayed stable.
- Comparison: all three packages replaced code, summary, total, term, compliance, note, and all seven inclusion rows; all states were distinct and reconciled.
- Projects: all 12 sector/region combinations exercised; the four industrial count mismatches and one social/volga row/detail mismatch reproduced consistently.
- Geometry: every `.mp-page` remained exactly 1920 × 1120; headers were 1834 × 72 and route content 1834 × 1048; no header/work-rail overlap or normal-state content clipping was found.
- Lower quarter: every route's meaningful lower band began at y=921, was 318px high, and contained 291-471 characters of route-specific content.
- Console: no relevant application warnings/errors; the temporary review server emitted one unrelated missing-favicon 404.

## Visual Evidence

The concept reference and all five final PNGs were inspected at original resolution. Every final PNG is 1920 × 1280 RGB and readable through the bottom edge.

- `01-cover.png`: strong industrial brand signal, hard-edged product photography, live offer rails, and lower product families.
- `02-catalog.png`: dense filter/ledger/detail anatomy and lower procurement conditions; the static image is visually coherent, while the Chrome filtered state exposes the row mismatch.
- `03-configurator.png`: closest route to the concept reference, with control rail, dual route-owned images, calculation result, blueprint cue, and full lower specification.
- `04-comparison.png`: distinct package matrix, architect evidence, replaced row states, and lower standards/documentation band.
- `05-projects.png`: dense project ledger, installation evidence, selected facts, and lower production timeline; the non-default industrial state visibly shows `12 проектов` beside seven rows.

The system follows the concept's graphite/white/orange technical language, compact B2B density, hard edges, and specification-led composition. No rounded SaaS card wall, decorative wireframe, fake 3D frame, or renderer-owned gradient was found.

## Assets And Ownership

- Exact route-owned URL occurrences passed: cover 1, catalog 1, configurator 2, comparison 1, projects 1.
- Each of the six Modulprof asset URLs occurs exactly once across all five route outputs and only on its assigned route.
- SHA-256 comparison against every other project-owned PNG found zero cross-project exact duplicates for all six Modulprof assets.

## Imports And Banned Patterns

- Imports at `portfolio/kwork_pack/sites/modulprof.py:3` are limited to `Mapping`, `escape_html`, `ProjectSpec`, `ShotSpec`, and `RenderedPage`.
- No legacy renderer, other project renderer, renderer stylesheet, route body, header, or interaction helper is imported.
- No gradient, overlay, border radius, decorative SVG/wireframe, placeholder copy, or legacy/template renderer pattern occurs in the new renderer.

## Verification

```text
python -m pytest tests/test_portfolio_product_systems_v2.py -k modulprof -q
10 passed, 25 deselected in 4.92s

python -m pytest tests/test_portfolio_quality.py -q
9 passed in 0.36s

python -m py_compile portfolio/kwork_pack/sites/modulprof.py tests/test_portfolio_product_systems_v2.py
exit 0

python -m portfolio.kwork_pack.cli validate --output artifacts/kwork-portfolio-v2 --project modulprof
Checked files: 5; issues: 0

git diff --check 60df87d..bd7c9b8
exit 0
```

The automated suites pass, but the independent Chrome combinations above demonstrate missing assertions and production-visible contract failures. Both mandatory verdicts therefore fail.
