# Kwork Send Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refuse Kwork replies that are unavailable, cannot expose a response count, or exceed the live response limit immediately before form interaction.

**Architecture:** Keep page parsing in `app.kwork_client`, add a pure replyability validator there, and call it from `KworkReplySender` before it opens the offer form. Thread `KWORK_MAX_RESPONSES` through GUI and Kwork web source constructors so direct and email approvals share the invariant.

**Tech Stack:** Python 3.10+, existing Chrome DevTools Kwork client, pytest.

## Global Constraints

- Do not submit, click, or mutate any live Kwork project during tests.
- Use the authenticated isolated Kwork Chrome profile through existing CDP code.
- Keep secrets in ignored `.env`; never log cookies, passwords, or keys.
- A missing live response count is a send refusal, not a guessed approval.

---

### Task 1: Pure Replyability Validation

**Files:**
- Modify: `src/app/kwork_client.py`
- Modify: `tests/test_kwork_client.py`

**Interfaces:**
- Produces `KworkProjectReplyabilityError(RuntimeError)` and
  `ensure_project_is_replyable(info: KworkProjectInfo, max_responses: int) -> KworkProjectInfo`.

- [ ] **Step 1: Write failing validator tests**

```python
with pytest.raises(KworkProjectReplyabilityError, match="7.*5"):
    ensure_project_is_replyable(KworkProjectInfo(..., response_count=7), 5)
assert ensure_project_is_replyable(KworkProjectInfo(..., response_count=5), 5).response_count == 5
```

- [ ] **Step 2: Run focused tests and confirm the missing import failure**

Run: `python -m pytest tests/test_kwork_client.py -q`

- [ ] **Step 3: Implement the validator**

```python
def ensure_project_is_replyable(info, max_responses):
    if info.is_unavailable:
        raise KworkProjectReplyabilityError("Kwork project is unavailable: ...")
    if not info.has_response_count:
        raise KworkProjectReplyabilityError("Kwork response count is unavailable; reply was not sent")
    if info.response_count > max_responses:
        raise KworkProjectReplyabilityError(
            f"Kwork project now has {info.response_count} responses; limit is {max_responses}"
        )
    return info
```

- [ ] **Step 4: Run focused tests and commit**

Run: `python -m pytest tests/test_kwork_client.py -q`

### Task 2: Sender-Level Live Preflight

**Files:**
- Modify: `src/app/kwork_sender.py`
- Modify: `tests/test_kwork_sender.py`

**Interfaces:**
- `KworkReplySender(..., max_responses: int | None = None)` calls
  `_ensure_project_is_replyable(contact)` before Chrome form navigation when
  `max_responses` is configured.

- [ ] **Step 1: Write a failing no-form-action test**

```python
sender = KworkReplySender(max_responses=5)
with pytest.raises(KworkProjectReplyabilityError, match="7.*5"):
    sender.send_message("https://kwork.ru/projects/123/view", "Здравствуйте!")
assert chrome_actions == []
```

- [ ] **Step 2: Run focused test and confirm it fails because preflight is absent**

Run: `python -m pytest tests/test_kwork_sender.py -q`

- [ ] **Step 3: Add a lazy `KworkProjectClient` inspection helper and call it from `send_reply`**

```python
if self.max_responses is not None:
    self._ensure_project_is_replyable(contact)
```

The helper must use `timeout_seconds`, `cdp_url`, and `browser_profile_dir`
from this sender and call the pure validator.

- [ ] **Step 4: Run focused sender tests**

Run: `python -m pytest tests/test_kwork_sender.py -q`

### Task 3: Thread Runtime Configuration And Document Behavior

**Files:**
- Modify: `src/app/gui.py`
- Modify: `src/app/kwork_source.py`
- Modify: `tests/test_gui.py`
- Modify: `tests/test_kwork_source.py`
- Modify: `README.md`

**Interfaces:**
- GUI sender and `KworkWebSource` sender pass `KWORK_MAX_RESPONSES` through to
  `KworkReplySender`.

- [ ] **Step 1: Write failing forwarding tests**

```python
assert FakeSender.last_kwargs["max_responses"] == 5
```

- [ ] **Step 2: Run focused tests and confirm the missing argument failure**

Run: `python -m pytest tests/test_gui.py tests/test_kwork_source.py -q`

- [ ] **Step 3: Pass the configured max response count into both constructors**

- [ ] **Step 4: Document preflight refusal in README**

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/test_gui.py tests/test_kwork_source.py tests/test_kwork_sender.py tests/test_kwork_client.py -q`

### Task 4: Verification And Publication

**Files:**
- Modify: `docs/superpowers/plans/2026-07-17-kwork-send-preflight.md`

- [ ] **Step 1: Run full verification**

Run: `python -m pytest -q`

Run: `python -m compileall -q src`

Run: `git diff --check`

- [ ] **Step 2: Mark completed steps, commit, and push**

Commit: `git commit -m "feat: preflight Kwork replies before sending"`
