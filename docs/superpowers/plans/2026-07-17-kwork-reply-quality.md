# Kwork Reply Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Kwork proposal quality, keep price out of customer messages, and add optional cloud vision fallback for unreadable attachments.

**Architecture:** The lead judge continues to produce structured scope and price data. A small deterministic quality gate turns the model draft into a customer-safe proposal and supplies a task-focused fallback. Attachment parsing remains local-first within the application, with OpenRouter vision used only after image or scanned-PDF OCR has no text.

**Tech Stack:** Python 3.10+, OpenAI-compatible SDK, DeepSeek, optional OpenRouter, PyMuPDF, Tesseract, pytest.

## Global Constraints

- Keep secrets in ignored `.env` only.
- Keep Cloud-only provider calls; do not invoke Ollama.
- Preserve existing Kwork browser and manual-approval behaviour.
- Use UTF-8 and retain compatibility with existing injectable test doubles.

---

### Task 1: Customer Reply Guard

**Files:**

- Modify: `src/app/ai_lead_judge.py`
- Modify: `tests/test_ai_lead_judge.py`

**Interfaces:**

- Produces: `clean_customer_reply(reply: str, summary: str, estimated_days: int) -> str`
- Produces: `parse_judge_response(raw: str) -> LeadJudgeResult` with a price-free `draft_reply`

- [ ] **Step 1: Write failing tests**

```python
def test_parse_judge_response_removes_price_and_generic_question():
    result = parse_judge_response(JSON_WITH_PRICE_AND_GENERIC_QUESTION)
    assert "руб" not in result.draft_reply.lower()
    assert "уточните детали" not in result.draft_reply.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai_lead_judge.py -q`

Expected: failure because the current parser keeps the price sentence.

- [ ] **Step 3: Implement the minimal guard and fallback**

```python
def clean_customer_reply(reply: str, summary: str, estimated_days: int) -> str:
    # Remove commercial/generic sentences; use a concrete fallback if weak.
```

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/test_ai_lead_judge.py -q`

Expected: PASS.

### Task 2: Optional OpenRouter Vision Fallback

**Files:**

- Modify: `src/app/config.py`
- Modify: `src/app/main.py`
- Modify: `src/app/attachments.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_attachments.py`

**Interfaces:**

- Produces: `AppConfig.openrouter_api_key`, `openrouter_base_url`, and `openrouter_vision_model`
- Produces: `describe_image_with_openrouter(content: bytes, extension: str, ...) -> str`

- [ ] **Step 1: Write failing configuration and dispatch tests**

```python
def test_load_config_reads_openrouter_vision_settings(...):
    assert config.openrouter_vision_model == "..."

def test_image_uses_vision_when_ocr_has_no_text(monkeypatch):
    assert "vision" in status
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py tests/test_attachments.py -q`

Expected: failure because no OpenRouter fields or vision dispatch exist.

- [ ] **Step 3: Implement optional OpenRouter fallback**

```python
if not extracted_text and openrouter_api_key:
    return vision_description
```

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/test_config.py tests/test_attachments.py -q`

Expected: PASS.

### Task 3: Documentation and Full Verification

**Files:**

- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Document the provider variables and price separation**
- [ ] **Step 2: Run `pytest -q`**
- [ ] **Step 3: Run `C:\\Users\\user\\.codex\\scripts\\harness.cmd gate`**
- [ ] **Step 4: Inspect git diff, commit, and push**
