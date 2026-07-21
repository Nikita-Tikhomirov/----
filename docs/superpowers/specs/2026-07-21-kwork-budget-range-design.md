# Kwork Budget Range Design

## Goal

For every Kwork lead, retain the buyer's desired budget and the maximum price Kwork allows, show both values in the Family Todo lead card, and prefill the proposed response price at 85% of the allowed maximum.

## Data Flow

1. The desktop Kwork inspector reads the rendered project page and extracts two independent facts:
   - `buyer_desired_budget_rub`: the buyer's stated target, such as `Желаемый бюджет покупателя: до 2 000 ₽`.
   - `kwork_max_price_rub`: the Kwork permitted ceiling, such as `Допустимый: до 6 000 ₽`.
2. The scanner stores the values locally with the lead and sends them to the lead hub API.
3. Laravel persists and returns both fields. The Flutter app renders them as source facts separate from the editable `proposal_price_rub`.
4. When `kwork_max_price_rub` is available, the scanner sets `proposal_price_rub` to 85% of that amount, rounded to the nearest 100 rubles. If it is not available, the existing AI estimate remains as the editable fallback and the mobile card explicitly says that Kwork's limit was not found.
5. Before a final Kwork reply is filled, the desktop sender re-inspects the live project. If it finds a current Kwork maximum, it clamps the approved price to that ceiling and reports the adjusted value back to the hub.

## Semantics

- The buyer's desired budget is informational. It is never used as the ceiling for the response price.
- The Kwork maximum is the upper bound permitted by the marketplace and is used as the source for the 15% discount calculation.
- `proposal_price_rub` is always user-editable. A user may select a lower price in Family Todo.
- A missing or malformed value never becomes `5000` solely because a budget parser failed. The AI estimate remains only when Kwork does not provide a usable maximum.

## Mobile Presentation

The detail screen displays a compact `Бюджет Kwork` block before the editable proposal fields:

- `Желаемый бюджет: до 2 000 руб.` or `не указан`.
- `Допустимый максимум: до 6 000 руб.` or `не найден`.
- `Цена отклика: 5 100 руб. (максимум −15%)` when automatically calculated.

The list card shows the permitted maximum and the response price when either value exists.

## Error Handling

- The parser accepts the wording currently rendered by Kwork and common variations of `желаемый бюджет`, `допустимый`, `до`, `руб.` and `₽`.
- When live re-checking cannot read a maximum, the saved lead value is retained; the sender does not invent a new price.
- If Kwork's reply form rejects a manually selected price, the existing form error remains visible and the mobile lead changes to `failed` with the server-reported reason.

## Verification

- Python unit tests cover parsing both Kwork figures, the 15% calculation, missing data, API payload propagation, and no fallback-to-5000 regression.
- Laravel tests cover ingestion, update, and serialization of both new fields.
- Flutter tests cover JSON decoding and display of the source budget block.
- A live dry-run verifies that an inspected Kwork project sends the exact source figures and a calculated price to the mobile API without submitting an external reply.
