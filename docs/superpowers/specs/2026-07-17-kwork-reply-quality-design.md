# Kwork Reply Quality Design

## Goal

Make every proposed Kwork reply sound like a capable human specialist, keep the
price separate for the Kwork form, and recover useful attachment context when
local text extraction or OCR cannot read a scan.

## Decisions

- `price_rub` remains structured lead data. It is shown in the email, summary,
  and Kwork price field, but is never included in `draft_reply`.
- The lead judge receives a stricter reply brief: identify the client’s main
  task, name two or three concrete actions, state a realistic delivery window,
  and finish with a calm start-ready statement. Generic questions and empty
  sales phrases are forbidden.
- A deterministic reply quality gate removes accidental price/budget sentences,
  generic clarification requests, and unusably short drafts. It falls back to a
  concrete, task-focused reply when a provider returns weak text.
- DeepSeek remains the default text judge. OpenRouter is an optional cloud
  vision fallback for images and scanned PDFs only after local extraction/OCR
  produces no readable text. Keys stay in the local `.env`.

## Data Flow

1. Kwork data and readable attachment content reach the DeepSeek lead judge.
2. The judge returns score, scope, days, independent `price_rub`, and a draft.
3. The quality gate returns a customer-safe draft with no commercial terms.
4. GUI/email display price from structured lead summary and fill it into Kwork
   only after approval.
5. Attachment processing uses local parsers and Tesseract first; OpenRouter
   vision is called only for unreadable image/PDF pages when configured.

## Error Handling

- A failed text/vision provider never prevents scanning: the current rule-based
  lead judge and attachment status report remain usable.
- Vision fallback records a specific status and concise extracted description.
- Provider secrets are read only from ignored local configuration and are never
  written to logs, UI, commits, or test output.

## Verification

- Unit tests prove that prices are removed from model drafts and deterministic
  fallback replies remain useful and price-free.
- Unit tests prove the reply prompt prohibits prices and generic questions.
- Unit tests prove OpenRouter configuration loading and image/PDF vision
  fallback dispatch without contacting the network.
- The full Python test suite validates existing scan, email, GUI, and sender
  behaviour.
