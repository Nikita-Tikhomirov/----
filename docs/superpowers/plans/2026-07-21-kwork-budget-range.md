# Kwork Budget Range Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show Kwork's desired and maximum budgets in Family Todo and default the proposal price to 15% below Kwork's maximum.

**Architecture:** The desktop scanner extracts normalized budget values from rendered Kwork text, stores them locally, and publishes them through the existing lead hub payload. Laravel persists the source values; Flutter renders them separately from the editable proposal price. The sender re-checks the live maximum before filling an approved reply.

**Tech Stack:** Python 3.10, pytest, SQLite, Laravel/PHP, Flutter/Dart, GitHub Actions APK release.

## Global Constraints

- Preserve the existing `Family Todo` package id and release signing key.
- Use UTF-8 and ASCII identifiers in source code.
- Never send an external Kwork reply as part of tests.
- Price calculation is `round(maximum * 0.85 / 100) * 100`.
- Use the AI price only if no valid Kwork maximum exists.

---

### Task 1: Extract and persist source budget values in the desktop scanner

**Files:**
- Modify: `src/app/kwork_client.py`
- Modify: `src/app/storage.py`
- Modify: `src/app/main.py`
- Modify: `tests/test_kwork_client.py`
- Modify: `tests/test_storage.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Produces `KworkProjectInfo.buyer_desired_budget_rub` and `KworkProjectInfo.kwork_max_price_rub`.
- Extends `Lead` with the same nullable integer fields.
- Produces `proposal_price_rub = round(kwork_max_price_rub * 0.85 / 100) * 100` when a maximum exists.

- [ ] Write parser and scanner tests for `Желаемый бюджет покупателя: до 2 000 ₽` plus `Допустимый: до 6 000 ₽`.
- [ ] Run the focused tests and confirm they fail because the fields do not exist.
- [ ] Add parser helpers, SQLite migration columns, lead fields, and the 15% calculation.
- [ ] Run focused tests and then `python -m pytest -q`.
- [ ] Commit `feat: retain Kwork budget range and price target`.

### Task 2: Carry the budget range through the lead hub API

**Files:**
- Modify: `src/app/lead_api_client.py`
- Modify: `tests/test_lead_api_client.py`
- Modify: `C:\Users\user\Desktop\weather\laravel_backend_vps\database\migrations\2026_07_21_001700_add_kwork_budget_range_to_leads.php`
- Modify: `C:\Users\user\Desktop\weather\laravel_backend_vps\app\Domain\Leads\LeadRepository.php`
- Modify: Laravel lead tests if present

**Interfaces:**
- Ingest and serialization expose nullable `buyer_desired_budget_rub` and `kwork_max_price_rub`.

- [ ] Write Python payload test and Laravel repository/controller test that expect both values.
- [ ] Run tests and confirm the new fields are absent.
- [ ] Add migration, ingest/update mapping, serialization, and Python payload fields.
- [ ] Run target tests, production PHP syntax checks, and deploy the migration/backend.
- [ ] Commit `feat: publish Kwork budget range to lead hub` in each repository.

### Task 3: Render and edit leads with source budget facts in Family Todo

**Files:**
- Modify: `C:\Users\user\Desktop\weather\mobile_app\lib\models\lead_models.dart`
- Modify: `C:\Users\user\Desktop\weather\mobile_app\lib\features\leads\lead_inbox_page.dart`
- Modify: `C:\Users\user\Desktop\weather\mobile_app\test\lead_inbox_page_test.dart`

**Interfaces:**
- `LeadItem` has nullable `buyerDesiredBudgetRub` and `kworkMaxPriceRub`.
- List and detail display the source facts and label the default calculated price.

- [ ] Write a widget/model test for source budget rendering and the `5 100` calculated proposal.
- [ ] Run the target Flutter test and confirm it fails.
- [ ] Add JSON decoding and compact budget presentation without removing editable price controls.
- [ ] Run Flutter target tests and analyzer.
- [ ] Commit `feat: show Kwork budget range in mobile leads`.

### Task 4: Verify live data flow and publish the mobile update

**Files:**
- Modify: `README.md` if user-facing budget behavior needs documentation.
- Modify: `.github/workflows/mobile-apk.yml` only if the build version needs incrementing.

- [ ] Run a scanner dry-run using a saved or mocked Kwork project with both figures; assert payload values and calculated price without submitting a reply.
- [ ] Verify production API returns both figures for the owner profile `+79679812438`.
- [ ] Run global harness smoke and repository-specific test suites.
- [ ] Push both repositories and wait for the mobile APK workflow to pass.
- [ ] Verify the release contains one `Family Todo` APK and report the installation link.
