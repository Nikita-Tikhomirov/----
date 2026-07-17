# Kwork Reply Pipeline Design

## Goal

Make every new Kwork proposal useful enough to send with minimal editing: it
must show understanding of the client's concrete problem, outline the work and
the verifiable result, stay concise, and never mention price. Price remains a
separate Kwork form field filled only after approval.

## Evidence And Problem

The current pipeline asks one DeepSeek request to both judge a lead and write
the proposal. Real historic drafts show the predictable failure mode: generic
phrases, invented claims, price leakage, and questions that do not help start
the work. The current delivery-time sanitizer protects the Kwork form, but an
email can still contain an older weak draft. Current attachment parsing also
uses OpenRouter vision only after OCR returns no text, even though screenshot
layout requirements can be missed by text-only OCR.

## Chosen Approach

Use a focused three-stage DeepSeek flow only for accepted leads:

1. The existing lead judge decides whether the job is suitable, estimates days,
   and keeps `price_rub` as internal structured data.
2. A reply composer receives a redacted factual brief with the task title,
   description, readable attachment evidence, and estimated days. It writes a
   4-5 sentence message of roughly 350-850 characters.
3. A reply reviewer checks grounding, specificity, factual claims, tone,
   commercial-term leakage, and unnecessary questions. A failed review gets
   one repair pass. If either provider call fails, a deterministic
   task-focused fallback is used.

OpenRouter remains a vision-only provider. When configured, `smart` vision
adds a visual description for screenshots and for unreliable scanned PDF/DOCX
content. It is not used to write replies. Local text extraction and Tesseract
remain first-line parsers and the application works when vision is unavailable.

## Reply Contract

The composer receives only customer-safe facts. Budget, price, payment,
discounts, and Kwork price fields are removed before the prompt is assembled.
The generated message must:

- name the main client outcome rather than repeat the full task;
- name two or three concrete actions supported by the task or attachment;
- state a realistic duration without price;
- describe what will be checked or delivered;
- contain at most one question, only when the supplied judge question is a
  genuine blocker;
- avoid empty phrases such as `обсудим детали`, false portfolio claims, and
  references to AI, GPT, or agents.

The deterministic guard is always applied after every model result. It catches
price, budget, payment, generic questions, excessive length, too few sentences,
and missing work verbs. A failed guard triggers repair or the fallback instead
of allowing a weak message into email or Kwork.

## Interfaces

`src/app/reply_composer.py` owns the text workflow:

```python
@dataclass(frozen=True)
class ReplyDraftContext:
    title: str
    task_summary: str
    source_text: str
    attachment_context: str
    estimated_days: int
    blocking_question: str = ""

@dataclass(frozen=True)
class ReplyQualityResult:
    approved: bool
    issues: tuple[str, ...]

def compose_customer_reply(
    context: ReplyDraftContext,
    seed_reply: str,
    api_key: str = "",
    model: str = "deepseek-chat",
) -> str: ...
```

`scan_once` builds the context after Kwork page and attachment inspection and
stores the composed result as `leads.draft_reply`. It accepts an injectable
composer for tests. Existing approval, GUI editing, storage, and Kwork sender
interfaces stay unchanged.

`src/app/attachments.py` gains a small quality classifier and vision mode:

- `fallback`: current behavior, vision only if local text is absent;
- `smart`: vision adds visual facts for image attachments and unreliable
  OCR/scanned document content;
- `off`: no cloud vision.

## Error Handling

- No provider or vision error rejects a lead by itself.
- A composer/reviewer failure falls back to the strongest locally safe draft.
- A vision failure leaves the original local extraction and a clear status.
- Secrets remain in the ignored `.env`; API keys are never included in logs,
  database fields, UI text, tests, or commits.

## Verification

- Unit tests cover price-free, task-specific, concise replies; generic and
  commercial drafts must be repaired or fall back.
- Integration tests prove `scan_once` persists the composed reply and sends
  that same text by email without changing stored Kwork price/days.
- Attachment tests cover smart vision for screenshots and noisy OCR while
  preserving local-only fallback.
- A no-send live preview runs against saved lead data to inspect an actual
  generated reply without opening or submitting a Kwork form.
