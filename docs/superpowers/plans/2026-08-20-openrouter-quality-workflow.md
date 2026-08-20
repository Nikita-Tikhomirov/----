# OpenRouter Quality Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перевести анализ Kwork-заказов и подготовку откликов на OpenRouter и сделать десктопный сценарий стабильным для чтения и одобрения одним действием.

**Architecture:** Общий OpenRouter gateway обслуживает JSON-анализ, генерацию/проверку отклика и выбор файлов архива. Анализ передаёт генератору структурированную цель клиента, план и единственный блокирующий вопрос. GUI обновляет очередь отдельно от открытой карточки и не перезаписывает её каждые пять секунд.

**Tech Stack:** Python 3.10+, OpenAI Python SDK через OpenRouter, Tkinter/ttk, SQLite, pytest.

**Spec:** `docs/superpowers/specs/2026-08-20-openrouter-quality-workflow-design.md`

## Global Constraints

- Все секреты остаются только в `.env`.
- DeepSeek не используется в критическом пути анализа, отклика или выбора файлов архива.
- Bitrix остаётся жёстко исключённым.
- Максимальный срок подходящего заказа остаётся 7 дней.
- Первый отклик не содержит цену или условия оплаты.
- В Kwork ничего не отправляется без явного `OK` пользователя.
- Повторный `OK` не создаёт повторный отклик.

---

### Task 1: OpenRouter gateway и конфигурация моделей

**Files:**
- Create: `src/app/llm_client.py`
- Modify: `src/app/config.py`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `tests/test_llm_client.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `OpenRouterResult(content: str, model: str)`.
- Produces: `openrouter_chat(..., primary_model: str, fallback_models: tuple[str, ...]) -> OpenRouterResult`.
- Produces config fields `openrouter_analysis_model`, `openrouter_reply_model`, `openrouter_fallback_models`.

- [ ] **Step 1: Write failing gateway and config tests**

```python
def test_openrouter_chat_passes_ordered_fallback_models(monkeypatch):
    result = openrouter_chat(
        api_key="or-test",
        base_url="https://openrouter.ai/api/v1",
        primary_model="anthropic/claude-sonnet-4.5",
        fallback_models=("openai/gpt-5.1", "openai/gpt-4.1"),
        messages=[{"role": "user", "content": "test"}],
    )
    assert captured["extra_body"]["models"] == ["openai/gpt-5.1", "openai/gpt-4.1"]
    assert result.content == "готовый ответ"

def test_load_config_reads_openrouter_text_models(monkeypatch):
    assert config.openrouter_analysis_model == "openai/gpt-5.1"
    assert config.openrouter_reply_model == "anthropic/claude-sonnet-4.5"
    assert config.openrouter_fallback_models == ("openai/gpt-4.1",)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m pytest tests/test_llm_client.py tests/test_config.py -q`

Expected: imports or new config fields fail.

- [ ] **Step 3: Implement the shared OpenRouter client and config fields**

The client must deduplicate fallback models, omit the primary from fallback, set `base_url`, use `extra_body={"models": [...]}`, and return the model reported by OpenRouter.

- [ ] **Step 4: Document environment variables**

Add exact examples to `.env.example` and explain in `README.md` that OpenRouter now powers text analysis and replies while `OPENROUTER_VISION_MODEL` remains responsible for images/documents.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/test_llm_client.py tests/test_config.py -q`

Expected: PASS.

### Task 2: Structured OpenRouter order analysis and archive selection

**Files:**
- Modify: `src/app/ai_lead_judge.py`
- Modify: `src/app/attachments.py`
- Modify: `src/app/main.py`
- Modify: `src/app/gui.py`
- Test: `tests/test_ai_lead_judge.py`
- Test: `tests/test_attachments.py`
- Test: `tests/test_main.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: `openrouter_chat` and OpenRouter config from Task 1.
- Produces: `LeadJudgeResult.blocking_question: str`.
- Produces: `select_archive_entries_with_ai(..., base_url, fallback_models) -> ArchiveSelection`.

- [ ] **Step 1: Add failing analysis tests**

```python
def test_judge_uses_openrouter_and_keeps_only_a_real_blocking_question(monkeypatch):
    result = judge_lead(order_text, api_key="or-test", model="openai/gpt-5.1")
    assert result.customer_goal == "получать рабочие заявки с формы"
    assert result.work_plan == ["проверить обработчик", "исправить отправку", "протестировать сценарий"]
    assert result.blocking_question == "Куда должны поступать заявки?"

def test_judge_leaves_blocking_question_empty_when_task_can_start():
    assert result.blocking_question == ""
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_ai_lead_judge.py tests/test_attachments.py -q`

Expected: missing field and DeepSeek-specific calls fail expectations.

- [ ] **Step 3: Replace DeepSeek analysis with OpenRouter**

Update the JSON prompt to make `blocking_question` mandatory but normally empty. Preserve deterministic Bitrix and hard-keyword rejection before any paid call. Include files/OCR in the same analysis context.

- [ ] **Step 4: Replace archive selection with OpenRouter**

Rename provider-specific functions and pass the common gateway settings through `build_attachment_report`. Rule-based selection remains the final fallback when OpenRouter is unavailable.

- [ ] **Step 5: Pass OpenRouter settings through scan and rejudge flows**

`scan_once`, `_scan_runtime_once`, `_refresh_and_rejudge_existing_lead` and `_rejudge_existing_lead` must use `openrouter_api_key`, `openrouter_base_url`, `openrouter_analysis_model` and `openrouter_fallback_models`.

- [ ] **Step 6: Run focused analysis tests**

Run: `python -m pytest tests/test_ai_lead_judge.py tests/test_attachments.py tests/test_main.py tests/test_gui.py -q`

Expected: PASS.

### Task 3: Human-quality reply pipeline

**Files:**
- Modify: `src/app/reply_composer.py`
- Modify: `src/app/main.py`
- Modify: `src/app/gui.py`
- Test: `tests/test_reply_composer.py`
- Test: `tests/test_main.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Consumes: `LeadJudgeResult.customer_goal`, `work_plan`, `risks`, `blocking_question`.
- Extends: `ReplyDraftContext` with `customer_goal`, `work_plan`, `risks`.
- Produces: a normalized 3-5 sentence reply between 220 and 650 characters when facts allow.

- [ ] **Step 1: Add failing quality tests using realistic bad replies**

```python
def test_writer_uses_customer_goal_and_work_plan_without_generic_filler(monkeypatch):
    reply = compose_customer_reply(context, "", api_key="or-test")
    assert "форм" in reply.lower()
    assert "провер" in reply.lower()
    assert "уточните детали" not in reply.lower()
    assert "цена" not in reply.lower()
    assert reply.count("?") == 0

def test_writer_asks_only_the_approved_blocking_question():
    assert reply.count("?") == 1
    assert "Куда должны поступать заявки?" in reply
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_reply_composer.py tests/test_main.py::test_scan_once_persists_composed_price_free_reply -q`

Expected: context fields or OpenRouter call expectations fail.

- [ ] **Step 3: Convert writer, reviewer and repair calls to OpenRouter**

Use `OPENROUTER_REPLY_MODEL` as primary. Feed the writer structured customer goal and work plan before raw facts. Keep deterministic commercial, unsupported-fact and question gates.

- [ ] **Step 4: Tighten style and fallback**

Set 3-5 sentences, target 220-650 characters, remove robotic openings and generic closings. The deterministic fallback must name the recognized task and at least two relevant actions without inventing technologies.

- [ ] **Step 5: Use the blocking question only when analysis marks it**

`main.scan_once` passes `judge_result.blocking_question`. GUI regeneration rebuilds the context from the stored structured summary and preserves the same rule.

- [ ] **Step 6: Run focused reply tests**

Run: `python -m pytest tests/test_reply_composer.py tests/test_main.py tests/test_gui.py -q`

Expected: PASS.

### Task 4: Stable desktop reading and one-click approval

**Files:**
- Modify: `src/app/gui.py`
- Test: `tests/test_gui.py`

**Interfaces:**
- Produces: `_replace_text_preserving_view(widget, value: str) -> None`.
- Changes: `refresh_leads(force_details: bool = False) -> None` does not reload details for the unchanged selected lead.
- Changes: `on_lead_select(..., force: bool = False)` loads text only after an actual lead change or explicit force.

- [ ] **Step 1: Add a failing regression test for the five-second refresh**

```python
def test_background_refresh_does_not_overwrite_open_lead_or_scroll_position():
    gui.current_lead_id = 17
    gui.reply_text.value = "Моя несохранённая правка"
    gui.summary_text.view = (0.45, 0.70)
    LeadFunnelGui.refresh_leads(gui)
    assert gui.reply_text.value == "Моя несохранённая правка"
    assert gui.summary_text.view == (0.45, 0.70)
```

- [ ] **Step 2: Run the GUI regression test and verify RED**

Run: `python -m pytest tests/test_gui.py -k "background_refresh or preserving_view" -q`

Expected: current implementation deletes and reinserts both texts.

- [ ] **Step 3: Separate queue refresh from detail loading**

Keep selected row by lead id but skip detail reload when that id did not change. Remove the duplicate direct `on_lead_select()` call when Tk already dispatches a selection event. Explicit lead changes still load all fields.

- [ ] **Step 4: Preserve viewport for legitimate summary updates**

The text helper stores `yview`, insert cursor and selection, changes content only if it differs, then restores the state. `summary_text` is read-only between updates; copy remains enabled. `reply_text` remains editable.

- [ ] **Step 5: Make one-click approval save the visible draft first**

Confirm `_lead_payload` reads the visible title, price, days and reply; `_save_lead_payload` runs before send; delivery blockers are shown before opening Kwork; existing `begin_lead_send` remains the idempotency guard.

- [ ] **Step 6: Run all GUI tests**

Run: `python -m pytest tests/test_gui.py -q`

Expected: PASS.

### Task 5: End-to-end verification and rollout

**Files:**
- Modify if needed: `README.md`
- No production submission to Kwork during automated verification.

**Interfaces:**
- Verifies the whole pipeline from fetched project facts to stored/published lead and dry-run approval preparation.

- [ ] **Step 1: Run the complete Python suite**

Run: `python -m pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run project smoke harness**

Run: `C:\Users\user\.codex\scripts\harness.cmd smoke`

Expected: exit code 0 in `CLOUD_ONLY` mode.

- [ ] **Step 3: Run live OpenRouter smoke without Kwork submission**

Use one realistic saved lead or a local fixture to call analysis and reply generation. Verify non-empty model names, structured analysis, no commercial terms and no more than one question. Do not call the Kwork submit button.

- [ ] **Step 4: Restart the desktop/mobile-control processes from the updated source**

Stop only the Grut `app.main mobile-control`/GUI process identified by exact command line and restart through the existing launchers. Confirm the Lead Hub heartbeat.

- [ ] **Step 5: Commit and push**

Run:

```powershell
git add -A
git commit -m "feat: make Kwork leads ready for one-click approval"
git push origin master
```

