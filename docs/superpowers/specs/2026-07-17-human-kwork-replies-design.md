# Human Kwork Replies Design

## Goal

Make regenerated and newly scanned Kwork replies sound like a competent web developer: focused on the buyer's result, concrete about the work, free of price discussion and free of routine clarification questions.

## Context

The current reply composer already removes prices, checks factual grounding, and performs a DeepSeek review. In practice, a draft can still contain several hidden requests for information such as "уточните" or "напишите" without question marks. The GUI regeneration path does not supply a blocking question, so any request for clarification there is unnecessary.

## Options Considered

1. Prompt-only wording. Smallest change, but a model can still ignore it and the unsafe text reaches the operator.
2. Rule-only rejection. Reliable for known phrases, but would over-reject natural, useful drafts and make the fallback trigger too often.
3. Layered guidance and validation. Make the intended behavior explicit to writer, reviewer, and repair prompts; reject unapproved questions or clarification imperatives deterministically; preserve one explicitly approved blocking question only in the scan path. This is the chosen approach.

## Behavior

- A `ReplyDraftContext` with no `blocking_question` permits no questions and no phrases asking the customer to clarify, provide, write, or send details.
- A context with one valid `blocking_question` permits that exact question only. Other questions and clarification requests are rejected.
- Writer and repair prompts state the same rule plainly. The reviewer receives the allowed question, if any, and rejects anything else.
- A reply cannot claim that a site already works or fails in a desktop/mobile environment that is absent from the source task. Writer, reviewer, and repair prompts also forbid unsupported current-state assertions.
- The final readiness sentence uses a direct first-person formulation, never asks the buyer to obtain an answer first.
- If the generated draft violates these rules, the existing repair pass runs. If repair remains invalid, the deterministic fallback is used; it also has no clarification request.
- Existing checks for commercial terms, AI mentions, generic phrases, factual task grounding, length, and concrete actions remain unchanged.

## Scope

Modify only `src/app/reply_composer.py`, its unit tests, and the README description of reply quality. No Kwork browser interaction, database schema, GUI widget, or provider configuration changes.

## Verification

- A normal context rejects one ordinary question and a hidden "уточните/напишите" request.
- A context with an allowed blocking question accepts that exact question and rejects a different one.
- A claim such as "на десктопе всё работает" is rejected when the task only describes the mobile version.
- The writer and repair prompts make the no-question condition explicit.
- The composer falls back safely when a provider output contains a prohibited clarification.
- The focused reply-composer tests and complete test suite pass.
