# Task 2 Report: Portfolio Visual Uniqueness

## Status

Review remediation is complete locally. The focused and expanded quality
contracts pass. The full suite has unrelated legacy renderer transition
failures noted under Concerns.

## Files Changed

- `portfolio/kwork_pack/quality.py`
- `portfolio/kwork_pack/validate.py`
- `tests/test_portfolio_quality.py`
- `tests/test_portfolio_validation.py`
- `tests/test_portfolio_assets.py`
- `tests/test_portfolio_manifest.py`

Review remediation additionally changed:

- `portfolio/kwork_pack/quality.py`
- `portfolio/kwork_pack/validate.py`
- `tests/test_portfolio_catalog.py`
- `tests/test_portfolio_quality.py`
- `tests/test_portfolio_validation.py`

No generated assets, site renderers, Kwork state, or the untracked design
inventory were modified.

## RED Evidence

Before implementation:

```text
python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q
ModuleNotFoundError: No module named 'portfolio.kwork_pack.quality'
```

The failure was the intended missing production module.

## GREEN Evidence

```text
python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q
17 passed in 4.16s

python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_assets.py tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py -q
34 passed in 4.43s

C:\Users\user\.codex\scripts\harness.cmd smoke
PASS (CLOUD_ONLY; local Ollama checks skipped)
```

Additional verification passed:

- `git diff --check`
- `python -m compileall -q portfolio/kwork_pack`
- UTF-8 CLI diagnostics: 75 missing screenshots and no replacement characters

## Thresholds

- dHash: 16x16 grayscale horizontal and vertical difference hash (512 bits).
- Asset and cross-project screenshot similarity: reject Hamming distance below
  12. This is under 2.5 percent changed hash bits, conservative enough to catch
  reused or minimally altered imagery without rejecting independently composed
  pages.
- Layout structure: a 12 by 8 tile fingerprint normalizes high-entropy photo
  tiles while preserving UI geometry. Cross-project screenshots at layout
  distance 8 or less are rejected.
- Lower viewport: variance at least 40, edge density at least 0.006, and at
  least 20 percent active detail tiles in the bottom 25 percent. All checks
  must pass, so a flat white tail or one thin divider cannot pass.

## Self-Review

- Exact duplicates use SHA-256 and stable `duplicate-asset` or
  `duplicate-screenshot` codes.
- Perceptual duplicates use stable `near-duplicate-*` codes and include both
  conflicting paths.
- Missing or invalid screenshots retain their primary validation issue and do
  not enter similarity checks.
- Fixtures now contain unique structured lower-band content rather than solid
  color placeholders.

## Review Remediation

The independent review marked the first Task 2 commit as CHANGES_REQUIRED.
Each finding received a regression test before implementation:

- Invalid declared assets now return stable `invalid-asset` issues and never
  abort `validate_pack`.
- Duplicate `AssetSpec` filenames are detected before physical paths are
  deduplicated; the catalog also requires unique declared filenames.
- Cross-project comparison keeps SHA-256 and dual-axis dHash checks, then adds
  a conservative UI-structure fingerprint so a swapped hero image cannot hide
  a reused layout.
- The lower band requires distributed active tiles as well as calibrated edge
  density, while a table fixture verifies normal dense UI content remains valid.
- Decodable wrong-format, wrong-size, and oversized screenshots still receive
  lower-band and cross-project similarity checks. Only missing or unreadable
  screenshots skip those computations.
- Screenshot issue paths and both conflicting paths are output-root-relative.

Review RED evidence:

```text
python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_catalog.py -q
7 failed, 26 passed

python -m pytest tests/test_portfolio_validation.py -q -k "reused_layout or clearly_different"
1 failed, 1 passed, 15 deselected
```

Review GREEN evidence:

```text
python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_catalog.py -q
36 passed in 15.95s

python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_assets.py tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py -q
45 passed in 16.25s
```

`git diff --check`, `python -m compileall -q portfolio/kwork_pack`, UTF-8 CLI
diagnostic checks, and the global smoke harness also passed.

## Commit

`aaa916e8c36fc8d4de307f2a54f790cd1681d7d1` - `feat: enforce portfolio visual uniqueness`

`4982c79774db14d984c8c15c263cde9af41f1e6e` - `fix: harden portfolio quality gates`

## Concerns

`python -m pytest -q` collected 511 tests and ended with 491 passed, 20 failed.
All failures are pre-existing Task 1 to Task 3 transition expectations in
`tests/test_portfolio_render.py` and `tests/test_portfolio_sites.py`: they
still assert four routes and three legacy render variants although the catalog
now declares five routes. Those renderers are explicitly outside Task 2 and
are replaced in Task 3, so they were not changed here.
