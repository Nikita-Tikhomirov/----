# Task 2 Report: Portfolio Visual Uniqueness

## Status

Completed within the Task 2 scope. The focused quality and catalog contracts
pass. The full suite has unrelated legacy renderer transition failures noted
under Concerns.

## Files Changed

- `portfolio/kwork_pack/quality.py`
- `portfolio/kwork_pack/validate.py`
- `tests/test_portfolio_quality.py`
- `tests/test_portfolio_validation.py`
- `tests/test_portfolio_assets.py`
- `tests/test_portfolio_manifest.py`

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

- dHash: 16x16 grayscale difference hash (256 bits).
- Asset and cross-project screenshot similarity: reject Hamming distance below
  12. This is under 5 percent changed hash bits, conservative enough to catch
  reused or minimally altered imagery without rejecting independently composed
  pages.
- Lower viewport: variance at least 40 and edge density at least 0.003 in the
  bottom 25 percent. Both checks must pass, so a flat white tail cannot pass on
  a nonblank upper viewport.

## Self-Review

- Exact duplicates use SHA-256 and stable `duplicate-asset` or
  `duplicate-screenshot` codes.
- Perceptual duplicates use stable `near-duplicate-*` codes and include both
  conflicting paths.
- Missing or invalid screenshots retain their primary validation issue and do
  not enter similarity checks.
- Fixtures now contain unique structured lower-band content rather than solid
  color placeholders.

## Commit

`aaa916e8c36fc8d4de307f2a54f790cd1681d7d1` - `feat: enforce portfolio visual uniqueness`

## Concerns

`python -m pytest` collected 500 tests and ended with 480 passed, 20 failed.
All failures are pre-existing Task 1 to Task 3 transition expectations in
`tests/test_portfolio_render.py` and `tests/test_portfolio_sites.py`: they
still assert four routes and three legacy render variants although the catalog
now declares five routes. Those renderers are explicitly outside Task 2 and
are replaced in Task 3, so they were not changed here.
