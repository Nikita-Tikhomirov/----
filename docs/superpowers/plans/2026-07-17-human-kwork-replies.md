# Human Kwork Replies Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent routine clarification requests and unnatural closing lines in generated Kwork replies while retaining a single explicitly approved blocking question.

**Architecture:** Keep `ReplyDraftContext.blocking_question` as the sole allow-list entry. Add deterministic request detection to `reply_quality_issues`, use it from writer/reviewer/repair prompts, and rely on the existing repair/fallback sequence for any invalid provider output.

**Tech Stack:** Python 3.10+, pytest, DeepSeek-compatible OpenAI client.

## Global Constraints

- Do not send Kwork messages during generation or tests.
- Do not expose or commit secrets.
- Keep replies price-free, factual, concise, and in Russian.
- Preserve the existing public `compose_customer_reply` interface.

---

### Task 1: Define no-question quality behavior

**Files:**
- Modify: `tests/test_reply_composer.py`
- Modify: `src/app/reply_composer.py`

**Interfaces:**
- Produces: `reply_quality_issues(reply: str, context: ReplyDraftContext) -> tuple[str, ...]`
- Consumes: `ReplyDraftContext.blocking_question`

- [x] **Step 1: Write failing tests**

```python
def test_quality_gate_rejects_question_and_hidden_clarification_without_allowed_question():
    issues = reply_quality_issues(
        "Здравствуйте! Проверю форму заявки и адаптив лендинга. Уточните, куда должны приходить заявки. После правок протестирую сценарий. Готов приступить сразу.",
        _form_context(),
    )
    assert "unapproved clarification" in issues


def test_quality_gate_allows_only_explicit_blocking_question():
    context = replace(_form_context(), blocking_question="К какой CRM нужно подключить форму?")
    issues = reply_quality_issues(
        "Здравствуйте! Проверю форму заявки и адаптив лендинга. К какой CRM нужно подключить форму? Затем внесу правки и протестирую сценарий. Готов приступить сразу.",
        context,
    )
    assert "unapproved clarification" not in issues
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/test_reply_composer.py -k clarification`

Expected: FAIL because `reply_quality_issues` currently permits the hidden clarification.

- [x] **Step 3: Implement minimal deterministic validation**

Add a normalized comparison against the one allowed blocking question and a narrow pattern for customer-facing clarification imperatives. Append `"unapproved clarification"` when the candidate violates that rule.

- [x] **Step 4: Run focused tests**

Run: `python -m pytest -q tests/test_reply_composer.py -k clarification`

Expected: PASS.

### Task 2: Align all model prompts with the rule

**Files:**
- Modify: `tests/test_reply_composer.py`
- Modify: `src/app/reply_composer.py`

**Interfaces:**
- Produces: `_writer_prompt(context)` and `_repair_prompt(candidate, issues, context)` with the allowed-question policy.

- [x] **Step 1: Write failing prompt assertions**

```python
def test_writer_prompt_forbids_questions_when_no_blocking_question():
    assert "не задавай вопросов" in _writer_prompt(_form_context()).lower()
```

- [x] **Step 2: Run test to verify failure**

Run: `python -m pytest -q tests/test_reply_composer.py -k writer_prompt`

Expected: FAIL because the current prompt does not explicitly prohibit questions when no question is supplied.

- [x] **Step 3: Implement prompt wording**

State that no question or request for details is allowed when the context has no approved question. When it has one, include it as the only allowed exact question. Mirror the rule in reviewer and repair prompts and prohibit indirect closing phrases that ask the buyer to obtain more information.

- [x] **Step 4: Run focused tests**

Run: `python -m pytest -q tests/test_reply_composer.py -k "writer_prompt or clarification"`

Expected: PASS.

### Task 3: Verify provider-output fallback and publish

**Files:**
- Modify: `tests/test_reply_composer.py`
- Modify: `README.md`

- [x] **Step 1: Write failing composer test**

Mock a generated candidate with `"Уточните..."` and a repair candidate with the same issue. Assert that `compose_customer_reply` returns the safe fallback without a clarification request.

- [x] **Step 2: Run test to verify failure**

Run: `python -m pytest -q tests/test_reply_composer.py -k prohibited_clarification`

Expected: FAIL because the existing quality gate accepts the generated text.

- [x] **Step 3: Implement only behavior required by the failing test**

Use the new quality result through the existing repair/fallback path. Document that ordinary details are not requested in the first message.

- [x] **Step 4: Run project verification**

Run: `python -m pytest -q`

Run: `python -m compileall -q src`

Run: `git diff --check`

Expected: all commands exit with code 0.

- [ ] **Step 5: Commit and push**

```powershell
git add src/app/reply_composer.py tests/test_reply_composer.py README.md docs/superpowers
git commit -m "fix: improve Kwork proposal quality"
git push origin master
```

### Task 4: Reject unsupported current-state claims

**Files:**
- Modify: `tests/test_reply_composer.py`
- Modify: `src/app/reply_composer.py`

**Interfaces:**
- Produces: `reply_quality_issues` issue `"unsupported current state"` for a claim about an environment not present in source facts.

- [x] **Step 1: Write the failing test**

`test_quality_gate_rejects_unconfirmed_current_state_claim` gives the composer a mobile-only task and a reply claiming that desktop already works.

- [x] **Step 2: Verify the test fails before the implementation**

Run: `python -m pytest -q tests/test_reply_composer.py -k unconfirmed_current_state`

Observed: FAIL because the original quality gate returned no issues.

- [x] **Step 3: Add the narrow fact guard and prompt policy**

Detect only state claims matching a named desktop/mobile environment. Compare the environment group against title, summary, source text, and attachment facts; reject an unmentioned environment. Add the same factual-grounding instruction to writer, reviewer, and repair prompts.

- [x] **Step 4: Run focused verification and real no-send preview**

Run: `python -m pytest -q tests/test_reply_composer.py -k "unconfirmed_current_state or writer_prompt"`

Observed: PASS. A DeepSeek preview for a mobile-only form task produced no question, no clarification request, no desktop claim, and no quality issues. It did not open Kwork or send a message.
