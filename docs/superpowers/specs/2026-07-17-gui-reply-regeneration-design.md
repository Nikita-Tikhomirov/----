# GUI Reply Regeneration Design

## Goal

Let the operator rewrite a weak historical Kwork proposal from the selected
lead directly in the GUI, using the current DeepSeek compose-review-repair
pipeline and saved order/attachment facts, without sending a Kwork reply or
silently overwriting stored data.

## Evidence

The current database contains historical leads created before the latest reply
pipeline. Their draft messages may contain price, references to AI, generic
questions, or unprofessional wording. A no-write live preview of the current
composer produces a substantially better grounded, price-free draft from the
same lead facts, but the GUI has no way to request that rewrite.

## Chosen Design

Add a `Пересобрать отклик` action to the selected lead controls. It snapshots
the selected title, duration, current text, Kwork card text, AI summary, and
stored attachment reports on the UI thread. A background worker passes that
snapshot to `compose_customer_reply` using the configured DeepSeek model.

The resulting text is placed in an in-memory pending-draft map keyed by lead
id and shown in the `Текст отклика` editor. It is not written to SQLite by the
rewrite action. The existing `Сохранить` and `OK и отправить отклик` actions
remain the only actions that persist the edited draft; the latter is still the
only one that can reach Kwork.

The pending draft remains visible if the user switches away and returns to the
lead during the same GUI session. A save removes the pending copy because the
database now holds that content.

## Error Handling

- Empty or synthetic order titles are rejected before the provider call.
- A provider error leaves the current draft and SQLite record untouched.
- The regenerate button is disabled while its worker is running to prevent
  duplicate token usage.
- A completed result is never sent by email or Kwork and never changes lead
  status.

## Verification

- Pure helper tests verify factual context includes attachment summaries and
  retains the user-selected title/duration.
- GUI tests prove regeneration queues a worker rather than sending, displays
  the returned pending draft, and clears it only when saved.
- Full pytest and compilation run with no live provider, email, or Kwork call.
