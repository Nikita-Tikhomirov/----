# Kwork Send Preflight Design

## Goal

Before a Kwork reply is filled or submitted, re-open the current project in
the authenticated Kwork Chrome session and refuse a stale, unavailable, or
overcrowded project. The same rule must apply to a direct GUI approval and to
the email approval route.

## Evidence

The local database contains historical leads whose projects are already
unavailable. The scan validates `Предложений: N`, but the number can change
between scan time and the operator clicking send. The user explicitly wants to
avoid replying after the configured response limit is exceeded.

## Chosen Design

`KworkReplySender` gains an optional `max_responses` constructor setting. When
it is set, `send_reply` performs a project inspection before it opens
`/new_offer` or fills a form. It uses the existing `KworkProjectClient` with
the same Chrome DevTools URL and isolated Kwork profile, so rendered,
authenticated page data is preferred.

`app.kwork_client` owns the pure validation rule. It turns a
`KworkProjectInfo` into a clear `KworkProjectReplyabilityError` when the
project is unavailable, when `Предложений` cannot be read, or when the count
is greater than `max_responses`. The exception text names the observed count
and configured limit where available.

Both production constructors pass the configured limit:

- `LeadFunnelGui._sender()` covers `OK и отправить отклик`.
- `KworkWebSource.send_message()` covers email-confirmed automatic replies.

No web form is modified unless the preflight succeeds. Existing sender callers
without `max_responses` retain their current behavior for backwards-compatible
tests and non-Kwork uses.

## Error Handling

- A closed or removed project is rejected before form navigation.
- A page without a readable response count is rejected rather than guessed.
- A count above the configured limit is rejected before submission.
- The GUI's existing error handling stores the reason on the lead and keeps it
  unsent; Kwork is not clicked.
- A normal Kwork success confirmation is still required after actual submit.

## Verification

- Unit tests prove the validator rejects unavailable, unreadable and over-limit
  projects, while accepting a count at the limit.
- Sender tests prove an over-limit preflight stops before Chrome/form actions.
- Web-source and GUI tests prove their sender construction forwards the
  configured limit.
- Full pytest, Python compilation and a no-send test suite run before commit.
