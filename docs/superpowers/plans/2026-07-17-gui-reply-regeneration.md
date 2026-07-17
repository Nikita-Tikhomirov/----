# GUI Reply Regeneration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a no-send, no-autosave GUI action that regenerates the selected Kwork proposal using the current composition pipeline.

**Architecture:** `gui.py` constructs a customer-safe `ReplyDraftContext` from the selected lead and saved attachment reports, starts an in-process background worker, and stores its result in `pending_replies`. Existing save/send actions persist the visible editor text and clear the pending draft only after their normal successful storage write.

**Tech Stack:** Python 3.10+, Tkinter, existing `app.reply_composer`, pytest.

## Global Constraints

- The regenerate action must never call the Kwork sender, email client, or storage write API.
- Use the configured cloud DeepSeek model only through `compose_customer_reply`; no Ollama.
- Keep provider secrets in `.env` and never render or log them.
- A generated customer message must stay price-free because the shared composer enforces that invariant.

---

### Task 1: Context And Pending-Draft Helpers

**Files:**
- Modify: `src/app/gui.py`
- Modify: `tests/test_gui.py`

**Interfaces:**
- Produces `_reply_context_from_lead(lead, title, days, attachments)` and
  `pending_replies: dict[int, str]` behavior.

- [x] **Step 1: Write failing helper tests**

```python
context = _reply_context_from_lead(lead, "Исправить форму", 2, [attachment])
assert context.title == "Исправить форму"
assert "ТЗ.pdf" in context.attachment_context
assert context.estimated_days == 2
```

- [x] **Step 2: Run test to confirm the missing helper failure**

Run: `python -m pytest tests/test_gui.py -q`

- [x] **Step 3: Add the minimal context helper**

- [x] **Step 4: Run focused helper tests**

Run: `python -m pytest tests/test_gui.py -q`

### Task 2: Background GUI Action

**Files:**
- Modify: `src/app/gui.py`
- Modify: `tests/test_gui.py`

**Interfaces:**
- `LeadFunnelGui.regenerate_selected_reply()` snapshots UI values and starts a
  worker; `_apply_regenerated_reply(lead_id, reply)` only changes the pending
  in-memory editor state.

- [x] **Step 1: Write failing no-send action tests**

```python
LeadFunnelGui._apply_regenerated_reply(dummy, lead.id, "Новый текст")
assert dummy.pending_replies[lead.id] == "Новый текст"
assert storage_writes == []
```

- [x] **Step 2: Run test to confirm the missing method failure**

Run: `python -m pytest tests/test_gui.py -q`

- [x] **Step 3: Add the button, worker, error path, and pending display**

- [x] **Step 4: Clear a pending reply only after `_save_lead_payload` writes it**

- [x] **Step 5: Run focused GUI tests**

Run: `python -m pytest tests/test_gui.py -q`

### Task 3: Document And Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-07-17-gui-reply-regeneration.md`

- [x] **Step 1: Document that regeneration is preview-only until Save or Send**

- [x] **Step 2: Run full verification**

Run: `python -m pytest -q`

Run: `python -m compileall -q src`

Run: `git diff --check`

- [x] **Step 3: Mark plan complete, commit, and push**

Commit: `git commit -m "feat: regenerate Kwork replies from GUI"`
