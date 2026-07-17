# Kwork RAR/7Z Attachment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Kwork scans extract relevant evidence from RAR and 7Z attachments through installed console archive tools, with the same bounded selection model as ZIP.

**Architecture:** Keep ZIP on `zipfile`. Add temporary-file adapters for `UnRAR`/`RAR` and `7z` that list names and bounded-stream selected entries; reuse `ArchiveEntryInfo`, DeepSeek selection, and `inspect_attachment` for the rest of the pipeline.

**Tech Stack:** Python 3.10+, built-in `subprocess`/`tempfile`, installed UnRAR/RAR and 7-Zip, pytest.

## Global Constraints

- Do not add package dependencies or install software.
- Never extract a whole archive to the workspace or send a Kwork response while reading attachments.
- Read at most `max_entries=8` selected files and at most `max_bytes` bytes per file.
- Bound console listings to 200 entry names and 256 KB before selection.
- Keep ZIP parsing behavior unchanged and preserve UTF-8 in reports and documentation.

---

### Task 1: Define console archive behavior with failing tests

**Files:**
- Modify: `tests/test_attachments.py`
- Modify: `src/app/attachments.py`

**Interfaces:**
- Produces: `_read_external_archive(...) -> tuple[list[str], ArchiveSelection]`
- Produces: `_rar_executable() -> Path | None` and `_seven_zip_executable() -> Path | None`

- [x] **Step 1: Write failing RAR/7Z integration tests**

```python
def test_build_attachment_context_opens_rar_and_reads_selected_inner_text(monkeypatch):
    monkeypatch.setattr("app.attachments._rar_executable", lambda: Path("C:/WinRAR/UnRAR.exe"))
    monkeypatch.setattr("app.attachments._list_rar_entries", lambda *_: ("notes.txt", "brief.txt"))
    monkeypatch.setattr("app.attachments._read_rar_entry", lambda _exe, _archive, name, _limit: b"Нужно сверстать форму" if name == "brief.txt" else b"мусор")
    result = build_attachment_report(("tz.rar: https://example.test/tz.rar",), output_dir=tmp_path, deepseek_api_key="")
    assert result.reports[0].status == "скачан, архив открыт"
    assert "brief.txt: прочитан" in result.reports[0].summary
```

- [x] **Step 2: Run the tests to verify failure**

Run: `python -m pytest -q tests/test_attachments.py -k rar`

Expected: FAIL because the former implementation only used the GUI WinRAR path.

- [x] **Step 3: Implement backend discovery, listing, and bounded streaming**

Add helpers that locate console `UnRAR`/`RAR` and `7z`, list archive entries, and stream selected file content with a timeout and `max_bytes + 1` cutoff. The stream helper kills its child process before raising `ValueError` for an oversize entry.

- [x] **Step 4: Route RAR/7Z through the existing selection and nested inspection pipeline**

Refactor the shared selection/inspection portion of `_read_zip_archive` into a backend-neutral helper. Use synthetic `ArchiveEntryInfo(size=None, kind=_archive_entry_kind(name))` for external archive names and report unknown sizes clearly.

- [x] **Step 5: Run focused tests**

Run: `python -m pytest -q tests/test_attachments.py -k "rar or zip"`

Expected: PASS.

### Task 2: Add failure and size-limit coverage

**Files:**
- Modify: `tests/test_attachments.py`
- Modify: `src/app/attachments.py`

- [x] **Step 1: Write failing tests for missing tooling and oversize entries**

```python
def test_rar_reports_missing_tool_without_failing_attachment_batch(monkeypatch):
    monkeypatch.setattr("app.attachments._rar_executable", lambda: None)
    context = build_attachment_context(("tz.rar: https://example.test/tz.rar",))
    assert "UnRAR/RAR не найден" in context


def test_rar_entry_over_limit_is_reported_and_not_inspected(monkeypatch):
    monkeypatch.setattr("app.attachments._read_rar_entry", lambda *_: (_ for _ in ()).throw(ValueError("файл больше лимита 10 байт")))
    assert "пропущен, файл больше лимита" in report.summary
```

- [x] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/test_attachments.py -k "missing_rar_tool or over_limit"`

Expected: FAIL until the new error mapping is implemented.

- [x] **Step 3: Map known adapter errors to readable attachment lines**

Return `скачан, архив не открыт` only when the archive cannot be listed. Keep `скачан, архив открыт` when listing succeeded and report individual skipped files inline.

- [x] **Step 4: Run focused tests**

Run: `python -m pytest -q tests/test_attachments.py -k "rar or zip or winrar"`

Expected: PASS.

### Task 3: Document and verify installed archive tools

**Files:**
- Modify: `README.md`

- [x] **Step 1: Document RAR/7Z support and the non-fatal fallback**

Replace the manual-only RAR/7Z note with the console-tool discovery behavior and status wording.

- [x] **Step 2: Run all project checks**

Run: `python -m pytest -q`

Run: `python -m compileall -q src`

Run: `git diff --check`

Expected: all commands exit with code 0.

- [x] **Step 3: Run no-send local RAR and 7Z smoke tests**

Create temporary RAR and 7Z archives from a small text fixture, list them through the new adapters, and confirm that their selected text is returned. Delete the temporary files after the command completes.

- [x] **Step 4: Commit and push**

```powershell
git add src/app/attachments.py tests/test_attachments.py README.md docs/superpowers
git commit -m "feat: read RAR and 7Z Kwork attachments"
git push origin master
```
