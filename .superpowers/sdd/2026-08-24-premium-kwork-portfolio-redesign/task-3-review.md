# Task 3 Independent Review

## Verdict

CHANGES_REQUIRED

## Scope

Reviewed the Task 3 specification, implementation plan, brief, report,
`e5dbdfa`, and the documentation commits `44e69bf` and `0690150` relative to
`1de42be`. No source files were modified.

## Findings

### HIGH - Dedicated renderer execution can incorrectly fall back to legacy

**File:** `portfolio/kwork_pack/sites/__init__.py:83`

The `try` block covers both `get_renderer(project)` and the returned renderer
call. If an already imported dedicated renderer raises `ModuleNotFoundError`
with `exc.name == project.renderer_module` while rendering, lines 85-88 treat
that execution failure as an absent module and silently render the legacy
page. This violates the brief's boundary that fallback is allowed only while
importing an absent declared module and that an existing dedicated renderer
must always take precedence.

Reproduced with a synthetic installed module whose callable raises
`ModuleNotFoundError(name=project.renderer_module)`: `render_site` returned a
legacy `RenderedPage` instead of propagating the error. Resolve the renderer
inside the narrow import `try`, then invoke it after the `except`. Add a test
where the callable itself raises this exact exception and assert that it
propagates without legacy dispatch.

### MEDIUM - The promised `RenderedPage` result is not enforced

**Files:** `portfolio/kwork_pack/sites/__init__.py:84`,
`tests/test_portfolio_site_registry.py:11`

`render_site` returns the dedicated callable's value unchanged, so a renderer
can return a string or any other object despite the concrete `RenderedPage`
return contract. The next layer assumes `.html`, `.css`, and `.scripts` at
`portfolio/kwork_pack/render.py:114`, turning the contract violation into a
later wrapped `AttributeError`. The registry tests conceal this gap by using a
separate `DedicatedPage` dataclass instead of the production `RenderedPage`.

Reproduced with an installed synthetic module returning `"plain string"`:
`render_site` returned `str`. Use the real runtime type in positive tests and
add a negative test with a diagnostic naming the project and module.

### MEDIUM - Desktop-only is not an enforced shell contract

**File:** `portfolio/kwork_pack/shell.py:34`

The shared shell still exports the old mobile renderer and `build_document`
selects it at lines 59-62. `Literal["desktop"]` is only a static annotation;
a replaced or externally constructed `ShotSpec(layout="mobile")` remains
accepted and produces mobile browser chrome. This leaves a reachable stale
mobile branch under a specification that excludes mobile screenshots.

Reproduced by passing such a shot to `build_document`; the result contained
`class="mobile-url-bar"`. Remove the mobile branch or reject any non-desktop
layout explicitly, and add a negative contract test rather than testing only
the current catalog's happy path.

### MEDIUM - Task 3 leaves a newly broken tracked test and documents it as deferred

**Files:** `tests/test_portfolio_sites.py:328`,
`.superpowers/sdd/2026-08-24-premium-kwork-portfolio-redesign/task-3-report.md:80`

Task 3 changes `render_site` from `str` to `RenderedPage` but does not update
the existing semantic-asset transition test, so it now raises `TypeError` at
line 330. The report acknowledges this new failure and says transition tests
must not be modified, but the brief prohibits modifying site-specific modules,
not their tests. A public return-type migration is incomplete while its tracked
caller test still uses the old type.

The other 15 failures in `tests/test_portfolio_sites.py` are inherited stale
four-variant assertions from the Task 1 catalog migration; they were not
introduced by `e5dbdfa`. They should still be reconciled so the suite is green,
but the new `RenderedPage` failure belongs directly to Task 3.

## Verified Areas

- `get_renderer_module` imports the declared string and enforces the required
  final module name derived from the slug.
- Missing and non-callable `render` attributes produce project/module-aware
  diagnostics.
- The semantic asset mapping is preserved, with the `hero` alias confined to
  the explicitly temporary legacy path.
- Page CSS is placed in the document head; trusted page scripts are appended
  after page markup as required.
- Dynamic shell metadata is escaped; raw HTML, CSS, and scripts remain within
  the brief's trusted project-owned boundary.
- Page, context, browser, and Playwright cleanup behavior remains covered and
  passed the targeted error test.

## Verification

```text
python -m pytest tests/test_portfolio_site_registry.py tests/test_portfolio_render.py tests/test_portfolio_shell.py -q
25 passed in 2.43s

python -m pytest tests/test_portfolio_catalog.py tests/test_portfolio_manifest.py tests/test_portfolio_quality.py tests/test_portfolio_validation.py -q
40 passed in 16.97s

tracked tests only: 504 passed, 16 failed in 28.53s
python -m compileall -q portfolio/kwork_pack
git diff --check 1de42be..0690150
```

The ordinary full-suite command also discovered two unrelated untracked Task 4
test files created during this review, so the recorded 504/16 result was run
against the tracked test set only.
