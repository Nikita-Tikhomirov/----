# Task 2 Independent Review

status: CHANGES_REQUIRED

Reviewed implementation commit: `aaa916e8c36fc8d4de307f2a54f790cd1681d7d1`

Reviewed report commit: `438f245312e48765b58785332d222a245c496e61`

Base commit: `e03e0b7100d6ae14314969d32e825c20dfdfe463`

## Findings

### HIGH - Invalid declared assets crash `validate_pack`

File: `portfolio/kwork_pack/quality.py:159` (integration caller:
`portfolio/kwork_pack/validate.py:146`)

`validate_asset_uniqueness` admits every regular file without checking that
Pillow can decode it, and `_uniqueness_issues` unconditionally calls `dhash`
for every candidate, even when there is only one file and therefore no pair to
compare. A declared asset containing `b"broken asset"` makes `validate_pack`
raise `PIL.UnidentifiedImageError` instead of returning a diagnostic report.
This violates the brief's requirement that invalid files be skipped by
similarity checks without obscuring their primary issue and turns the CLI into
only a generic command failure. There is no invalid-asset integration test.

### HIGH - Reusing one declared asset path is silently accepted

File: `portfolio/kwork_pack/quality.py:136`

The conversion to `set(paths)` removes duplicate declarations before pair
detection. Two distinct `AssetSpec` entries with the same filename therefore
resolve to one physical path and produce no `duplicate-asset` issue. A direct
probe with two unique asset keys sharing one filename returned zero issues.
The catalog test checks unique asset keys but not unique filenames, so a
project can appear to declare six assets while actually reusing fewer files.
This is a direct false negative against the original-asset contract.

### HIGH - Whole-image dHash does not enforce cross-project layout uniqueness

File: `portfolio/kwork_pack/quality.py:159`

Screenshot similarity is based on one 16x16 dHash of the complete rendered
image. A probe using two screenshots with the same header, content grid,
cards, footer, and geometry but different hero bitmap content produced Hamming
distance 79 and no issue at the configured threshold of 12. This is the exact
reused-layout case the design audit says the gate must reject; changing the
photograph can dominate the hash while preserving the template. The only
cross-project test at `tests/test_portfolio_validation.py:94` copies identical
bytes, so it exercises the SHA branch, not perceptual screenshot detection.

### HIGH - A virtually empty lower viewport passes both metrics

File: `portfolio/kwork_pack/validate.py:107`

The global variance and raw edge count can be satisfied by negligible
decoration. A 1920x1280 white image with only one two-pixel black horizontal
line in the lower quarter measured variance `403.8662` and edge density
`0.003131`, so it passes both configured thresholds while more than 99% of the
band remains blank. The content-bearing fixture at
`tests/test_portfolio_quality.py:113` is a synthetic field of stripes and does
not cover a mostly empty band with a divider. The gate therefore does not
enforce meaningful lower-band content as required.

### MEDIUM - Horizontal-only dHash produces deterministic false positives

File: `portfolio/kwork_pack/quality.py:33`

The hash compares only left/right neighbors. Any image whose rows are
horizontally constant hashes to zero regardless of vertical content. A smooth
vertical grayscale gradient and alternating high-contrast horizontal bands
had Hamming distance 0 and were reported as `near-duplicate-asset`, despite
being visibly different. No test establishes a conservative non-duplicate
case or threshold boundary; the near-duplicate test at
`tests/test_portfolio_quality.py:72` only asserts that some issue is returned.

### MEDIUM - Valid files with other issues are excluded from quality gates

File: `portfolio/kwork_pack/validate.py:102`

`if image_issues: continue` skips lower-band and screenshot-pair checks for
all prior issues, not only missing or invalid files. A decodable PNG that is
oversized or has wrong dimensions is omitted from duplicate detection, so
those conditions can hide a `duplicate-screenshot` or
`near-duplicate-screenshot` issue. The brief specifically permits skipping
missing or invalid files; it does not permit every format, size, or dimension
diagnostic to suppress the new quality checks. Existing tests assert the
legacy issue but do not assert that uniqueness remains active.

### MEDIUM - Screenshot duplicate diagnostics expose unstable absolute paths

File: `portfolio/kwork_pack/quality.py:115`

Asset diagnostics are normalized relative to the output root, but screenshot
diagnostics use `path.as_posix()`. With an absolute output root, both
`ValidationIssue.file` and the two paths in its message contain the complete
machine-specific temp/output path. A direct probe returned
`C:/Users/user/AppData/Local/Temp/.../one.png`. This is inconsistent with the
stable relative paths used by `validate_pack` and makes diagnostics and
snapshots environment-dependent. The cross-project test checks only slugs in
the message and never checks `issue.file` or root-relative conflicting paths.

## Verification

Focused Task 2 suite:

`python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q`

Result: `17 passed in 4.51s`.

Expanded quality/catalog suite:

`python -m pytest tests/test_portfolio_quality.py tests/test_portfolio_validation.py tests/test_portfolio_assets.py tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py -q`

Result: `34 passed in 4.81s`.

Full suite:

`python -m pytest -q`

Result: `480 passed, 20 failed in 15.72s`. The 20 failures match the report's
known Task 1-to-Task 3 legacy renderer expectations and are not additional
Task 2 findings.

Global harness smoke passed in `CLOUD_ONLY` mode. `git diff --check
e03e0b7..438f245` also passed.

## Decision

CHANGES_REQUIRED. The current tests are green but do not establish the core
behavior: invalid assets can abort validation, repeated declared files can be
erased before pair detection, reused layouts can evade screenshot dHash, and
an effectively empty lower band can pass the density gate.
