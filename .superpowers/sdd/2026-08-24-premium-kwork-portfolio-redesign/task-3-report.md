# Task 3 Report: Dedicated Site Renderer Runtime

## Status

Implementation is complete locally. The dedicated renderer runtime, browser
shell handoff, and five-desktop-shot tests are committed in `e5dbdfa`.

## Files Changed

- `portfolio/kwork_pack/sites/runtime.py`
- `portfolio/kwork_pack/sites/__init__.py`
- `portfolio/kwork_pack/render.py`
- `portfolio/kwork_pack/shell.py`
- `tests/test_portfolio_site_registry.py`
- `tests/test_portfolio_render.py`
- `tests/test_portfolio_shell.py`

No legacy site module, generated artifact, design inventory, or Kwork state
was modified.

## RED Evidence

Before the runtime implementation:

```text
python -m pytest tests/test_portfolio_site_registry.py tests/test_portfolio_render.py tests/test_portfolio_shell.py -q
10 failed, 15 passed
```

Failures established the missing registry APIs, the legacy string return value,
the missing dependency-import boundary, five-desktop-shot expectations, and
the missing page script parameter.

## GREEN Evidence

```text
python -m pytest tests/test_portfolio_site_registry.py tests/test_portfolio_render.py tests/test_portfolio_shell.py -q
25 passed in 2.41s

python -m pytest tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q
40 passed in 16.65s

python -m compileall -q portfolio/kwork_pack
git diff --check
```

The compile and diff checks completed with exit code 0. The global smoke
harness passed in `CLOUD_ONLY` mode.

## Migration Boundary

- `get_renderer_module` imports only `project.renderer_module` and verifies its
  final module name against the project slug.
- `get_renderer` rejects missing or non-callable `render` attributes with the
  project and declared module in the diagnostic.
- `render_site` prioritizes a dedicated renderer immediately when it exists.
- Legacy dispatch is loaded lazily and used only when importing the exact
  declared dedicated module raises `ModuleNotFoundError` for that module.
- A missing dependency from an existing dedicated module propagates unchanged.
- Legacy family modules remain on disk and are not modified; Task 8 removes
  the fallback after all dedicated modules exist.

## Self-Review

- Registry tests cover exact module selection, final-name mismatch, missing
  render, dedicated priority, migration fallback, and dependency failures.
- Render tests use semantic asset keys, assert five 1920x1280 desktop outputs,
  semantic URLs, no mobile frame, and browser cleanup.
- Shell tests assert page-owned CSS plus trusted scripts after page markup.
- No user data is added to raw script text.

## Full Suite Concern

```text
python -m pytest -q
504 passed, 16 failed in 27.36s
```

All 16 failures are in the unchanged `tests/test_portfolio_sites.py`: 15 still
assert four legacy renderer variants even though Task 1 defines five routes,
and one still expects `render_site` to return a string. They are intentionally
deferred because this task must not modify legacy site-specific renderers or
their transition tests.

## Commit

`e5dbdfa` - `refactor: isolate portfolio site renderers`

## Publication Concern

The required publish bootstrap created `origin`, but its push attempt failed
because the configured GitHub credential was rejected. A final push is still
attempted after this report commit.
