# Task 2 Final Re-review

status: APPROVED

Reviewed fix commit: `4982c79774db14d984c8c15c263cde9af41f1e6e`

Reviewed report commit: `f295a6b6e50e08e6ea1cbfde7af2629612a5653c`

Previous review commit: `875b98f3af908eb88127c9b8d8b257dbbbe2f784`

Original implementation commit: `aaa916e8c36fc8d4de307f2a54f790cd1681d7d1`

Base commit: `e03e0b7100d6ae14314969d32e825c20dfdfe463`

## Findings

No remaining blocking findings.

## Verified Resolutions

### Invalid assets no longer abort validation

`portfolio/kwork_pack/quality.py:231` decodes each uniqueness candidate inside
the diagnostic boundary and removes unreadable files before SHA and pair
comparison. A direct `validate_pack` probe with `b"broken asset"` returned one
stable `invalid-asset` issue at
`assets/tochka-hoda/workshop-hero.png`; no exception escaped.

### Repeated asset declarations are detected before path deduplication

`portfolio/kwork_pack/quality.py:161` retains all semantic keys for each
resolved path and emits `duplicate-asset` for every conflicting key pair. A
direct project with `first` and `second` both resolving to `shared.png`
returned the expected issue. The catalog additionally requires unique asset
filenames.

### Reused layouts are detected without observed realistic false positives

`portfolio/kwork_pack/quality.py:109` adds a 12 by 8 structure fingerprint in
addition to SHA-256 and dual-axis dHash. Re-running the original same-layout
probe with unrelated high-entropy hero images produced dHash distance 116 but
layout distance 0, and `validate_pack` returned
`near-duplicate-screenshot`.

The false-positive check generated five independently composed page types:
operations dashboard, product catalog, booking workflow, editorial feature,
and dense data-table application. All ten cross-type pairs were accepted.
Their layout distances ranged from 45 to 86 and dHash distances from 198 to
247, comfortably outside both duplicate thresholds.

### Lower-band coverage rejects token decoration and accepts a real table

`portfolio/kwork_pack/quality.py:60` requires distributed active tiles, and
`portfolio/kwork_pack/validate.py:111` combines coverage with variance and
edge density. The original white lower band with one two-pixel divider now
returns `sparse-lower-viewport`.

A five-shot direct `validate_pack` probe used a normal table with actual Arial
text, five columns, six rows, light backgrounds, and one-pixel row separators.
Every shot measured variance 673.4, edge density 0.0440, and coverage 0.781;
none received a sparse-lower-viewport issue. A second standalone realistic
table measured variance 697.8, edge density 0.0441, and coverage 0.854.

### Dual-axis dHash resolves the prior directional false positive

`portfolio/kwork_pack/quality.py:31` now records both horizontal and vertical
comparisons. The prior smooth vertical gradient versus alternating horizontal
bands probe produced Hamming distance 128 and no uniqueness issue, instead of
the former distance 0 false positive.

### Decodable legacy violations remain eligible for quality checks

`portfolio/kwork_pack/validate.py:104` separates decode success from format,
dimension, and file-size issues. Focused tests cover wrong format, wrong
dimensions, and oversized files. A direct wrong-dimension probe returned both
the 1920x1280 diagnostic and `near-duplicate-screenshot`.

### Screenshot diagnostics are stable and output-root-relative

`portfolio/kwork_pack/quality.py:202` receives the validation root and renders
conflicting screenshot paths relative to it. A direct absolute-temp-root probe
returned `dentalea/01-cover.png` and `tochka-hoda/01-cover.png`; neither the
issue file nor message contained the temp root.

## Verification

Focused remediation suite:

`python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_catalog.py -q`

Result: `36 passed in 16.31s`.

Expanded quality/catalog suite:

`python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_assets.py tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py -q`

Result: `45 passed in 17.21s`.

Full suite:

`python -m pytest -q`

Result: `491 passed, 20 failed in 26.99s`. The 20 failures are the already
documented Task 1-to-Task 3 legacy renderer expectations in
`tests/test_portfolio_render.py` and `tests/test_portfolio_sites.py`; they are
not Task 2 regressions.

`python -m compileall -q portfolio/kwork_pack`, both Task 2 scoped
`git diff --check` commands, and the global harness smoke all passed. Harness
reported `CLOUD_ONLY` with local Ollama checks disabled as required.

## Decision

APPROVED. Commits `4982c79` and `f295a6b` close every prior Task 2 finding,
the focused contracts pass, realistic lower-band table content remains
accepted, and independent cross-layout probes found no false positives.
