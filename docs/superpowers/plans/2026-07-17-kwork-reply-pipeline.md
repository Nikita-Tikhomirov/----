# Kwork Reply Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate grounded, price-free Kwork proposals through a separate compose-review-repair path and extract more useful visual evidence from attachments.

**Architecture:** `ai_lead_judge.py` continues to own fit scoring and structured proposal terms. A new `reply_composer.py` owns redaction, deterministic checks, DeepSeek composition/review, repair, and fallback generation. `main.py` injects this component after a lead passes the judge. `attachments.py` retains local parsing but adds explicit vision modes and uses OpenRouter only for visual evidence.

**Tech Stack:** Python 3.10+, OpenAI-compatible SDK, DeepSeek, optional OpenRouter vision, PyMuPDF, Tesseract, pytest.

## Global Constraints

- Keep all secrets in ignored `.env` only.
- Keep Cloud-only provider calls and never invoke Ollama.
- Never place price, budget, payment, or discounts in `draft_reply`.
- Preserve manual email approval and do not submit a Kwork reply during tests.
- Keep injectable dependencies for unit and integration tests.

---

### Task 1: Reply Composer And Deterministic Guard

**Files:**
- Create: `src/app/reply_composer.py`
- Create: `tests/test_reply_composer.py`

**Interfaces:**
- Produces: `ReplyDraftContext`, `ReplyQualityResult`, and `compose_customer_reply(...) -> str`.
- Consumes: `clean_customer_reply` only as the final commercial-term safety net.

- [x] **Step 1: Write failing quality tests**

```python
def test_compose_rejects_price_and_generic_reply_without_provider():
    context = ReplyDraftContext(
        title="Исправить форму заявки",
        task_summary="Исправить форму и адаптив лендинга",
        source_text="Форма не отправляется на мобильном.",
        attachment_context="",
        estimated_days=2,
    )
    reply = compose_customer_reply(
        context,
        "Здравствуйте! Цена 5000 руб. Уточните детали.",
    )
    assert "руб" not in reply.lower()
    assert "уточните детали" not in reply.lower()
    assert "форм" in reply.lower()
```

- [x] **Step 2: Run the focused test and confirm the missing module failure**

Run: `python -m pytest tests/test_reply_composer.py -q`

Expected: collection fails because `app.reply_composer` does not exist.

- [x] **Step 3: Implement factual redaction, quality checks, and deterministic fallback**

```python
def compose_customer_reply(context, seed_reply, api_key="", model="deepseek-chat"):
    candidate = _safe_candidate(seed_reply, context)
    return candidate if not reply_quality_issues(candidate, context) else _fallback_reply(context)
```

The fallback selects actions from task keywords such as form, layout, WordPress,
domain, API, or generic site fix. It describes only actions that are supported
by the supplied context.

- [x] **Step 4: Add provider composition and one repair pass behind the same interface**

```python
if api_key:
    candidate = _compose_with_deepseek(context, api_key, model) or candidate
    review = _review_with_deepseek(candidate, context, api_key, model)
    if not review.approved:
        candidate = _repair_with_deepseek(candidate, review.issues, context, api_key, model)
```

- [x] **Step 5: Run focused tests and commit**

Run: `python -m pytest tests/test_reply_composer.py -q`

Expected: PASS.

Commit: `git commit -m "feat: add Kwork reply quality pipeline"`

### Task 2: Scan Integration And Email Safety

**Files:**
- Modify: `src/app/main.py`
- Modify: `tests/test_main.py`
- Modify: `README.md`

**Interfaces:**
- `scan_once(..., reply_composer=compose_customer_reply)` persists the composer output.
- `reply_composer` receives `ReplyDraftContext`, `seed_reply`, `api_key`, and `model`.

- [x] **Step 1: Write an integration test with a price-leaking judge draft**

```python
def test_scan_once_persists_composed_price_free_reply(...):
    created = scan_once(..., lead_judge=fake_judge, reply_composer=fake_composer)
    lead = storage.list_leads(status="emailed")[0]
    assert lead.draft_reply == "Проверю форму и адаптив, затем протестирую отправку."
    assert lead.proposal_price_rub == 5000
```

- [x] **Step 2: Run the focused test and confirm the new argument failure**

Run: `python -m pytest tests/test_main.py::test_scan_once_persists_composed_price_free_reply -q`

Expected: FAIL because `scan_once` has no `reply_composer` parameter.

- [x] **Step 3: Build a redacted reply context in `scan_once` and call the composer**

```python
reply_context = ReplyDraftContext(
    title=_proposal_title_from_text(post.text, judge_result.summary),
    task_summary=judge_result.summary,
    source_text=_reply_source_text(post, project_info),
    attachment_context=attachment_context,
    estimated_days=judge_result.estimated_days,
    blocking_question=judge_result.questions[0] if judge_result.questions else "",
)
draft_reply = reply_composer(reply_context, judge_result.draft_reply, ...)
```

`_reply_source_text` must omit Kwork budget, price, payment, and form terms.

- [x] **Step 4: Run focused integration tests and commit**

Run: `python -m pytest tests/test_main.py tests/test_reply_composer.py -q`

Expected: PASS.

Commit: `git commit -m "feat: compose Kwork replies after lead evaluation"`

### Task 3: Smart OpenRouter Vision Evidence

**Files:**
- Modify: `src/app/config.py`
- Modify: `src/app/main.py`
- Modify: `src/app/attachments.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_attachments.py`
- Modify: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Adds `AppConfig.openrouter_vision_mode: str` loaded from `OPENROUTER_VISION_MODE`.
- `inspect_attachment(..., openrouter_vision_mode="smart")` returns combined local and vision evidence where useful.

- [ ] **Step 1: Write failing smart-vision tests**

```python
def test_image_in_smart_mode_keeps_ocr_and_adds_vision(monkeypatch):
    status, text = inspect_attachment(..., openrouter_api_key="or-test", openrouter_vision_mode="smart")
    assert status == "скачан, OCR + vision прочитан"
    assert "OCR:" in text and "Vision:" in text
```

- [ ] **Step 2: Run focused tests and confirm the new argument failure**

Run: `python -m pytest tests/test_attachments.py tests/test_config.py -q`

Expected: FAIL because the vision mode is not present.

- [ ] **Step 3: Implement `off`, `fallback`, and `smart` modes**

```python
if mode == "smart" and _vision_should_enrich(kind, local_text):
    vision_text = describe_image_with_openrouter(...)
```

`smart` enriches screenshots and visibly unreliable OCR. `fallback` retains the
existing no-text behavior. A failed call leaves the local result untouched.

- [ ] **Step 4: Thread mode through `main.py`, document it, and run focused tests**

Run: `python -m pytest tests/test_attachments.py tests/test_config.py tests/test_main.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `git commit -m "feat: enrich unreadable Kwork attachments with vision"`

### Task 4: End-To-End Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Verify all new settings and operator behavior are documented**

Document `OPENROUTER_VISION_MODE=smart` and the price-free reply invariant.

- [ ] **Step 2: Run all Python tests and compile checks**

Run: `python -m pytest -q`

Expected: PASS.

Run: `python -m compileall -q src`

Expected: exit code 0.

- [ ] **Step 3: Run a no-send composition check with a local test fixture**

Run: `python -m pytest tests/test_reply_composer.py tests/test_main.py -q`

Expected: the generated reply is price-free, persisted only in the temporary
test database, and no Kwork browser or email sender is invoked.

- [ ] **Step 4: Inspect final diff, commit, and push**

Run: `git diff --check`

Expected: no output.

Commit: `git commit -m "docs: explain Kwork reply quality controls"`
