# Tochka Hoda Design Inventory

## References

- Home: `artifacts/kwork-portfolio-v2/concepts/tochka-hoda-home.png`
- Diagnostics: `artifacts/kwork-portfolio-v2/concepts/tochka-hoda-diagnostics.png`
- Booking: `artifacts/kwork-portfolio-v2/concepts/tochka-hoda-booking.png`
- Case study: `artifacts/kwork-portfolio-v2/concepts/tochka-hoda-case.png`
- Prices: `artifacts/kwork-portfolio-v2/concepts/tochka-hoda-prices.png`

These five images are authoritative composition references. The implementation
may correct generated-image spelling and data inconsistencies, but it must not
change the visible hierarchy, density, layout family, or image treatment.

## Design System

- Canvas: 1920x1280 desktop browser screenshot; site viewport below shared
  browser chrome must remain dense through the bottom band.
- Background: true white with cool neutral borders; no cream tint, gradient,
  overlay, glow, or decorative background shape.
- Accent: service red around `#ed0b16`; primary text near black; supporting
  text neutral gray; green appears only for a confirmed state or valid result.
- Typography: wide geometric sans for the wordmark and a restrained grotesk
  for content. Large page titles are compact and left aligned; controls and
  tables use deliberate 14-18 px desktop sizing.
- Geometry: square or lightly rounded controls (0-6 px), thin neutral borders,
  almost no shadows. Cards are reserved for selectors, summaries, and framed
  evidence rather than page sections.
- Header: wordmark left, six text navigation items, phone and hours, one red
  booking command. Preserve this anatomy on every route.
- Icons: consistent red outline set, 2 px optical stroke, no emoji or text
  glyph substitutes.
- Photography: bright, clean, realistic service environment; neutral lighting;
  no dark cinematic grade; each route uses a different generated photograph.

## Route Inventory

### `/`

- H1: `Техническое обслуживание вашего автомобиля`.
- Hero split: offer and diagnostic action left, workshop/car photography right.
- Required proof: 41-parameter diagnostic, 990 rubles, 24-month warranty,
  ten years of experience, qualified specialists, more than 12,000 clients.
- Bottom continuation: six service categories with concise descriptions.
- Photo role: `workshop_hero` only.

### `/uslugi/diagnostika-avtomobilya`

- H1: `Диагностика автомобиля`; supporting line: `41 параметр проверки`.
- Package selector: `Базовая`, `Комплексная`, `Перед покупкой`.
- Selected package shows included checks, duration, price, and booking command.
- Bottom continuation: grouped 41-point checklist, not generic feature cards.
- Photo role: `diagnostic_closeup` only.

### `/zapis/diagnostika`

- H1: `Запись на диагностику`.
- Four numbered sections: car, service, date/time, contacts.
- Filled state: BMW X5, A123BC777, comprehensive diagnostic, 26 August 2026,
  11:30, realistic Moscow contact data.
- Right summary includes duration, address, total, and confirmation command.
- Bottom continuation: visit timeline plus preparation notes.
- Photo role: `service_lounge` only.

### `/raboty/bmw-x5-hodovaya`

- H1: `BMW X5: устранили стук в ходовой`.
- Facts: BMW X5 F15, 2018, 89,420 km, one day, 78,650 rubles.
- Evidence sequence: complaint, diagnostics, verdict, findings, completed work,
  parts and labor, alignment result, client quote, warranty.
- Photo roles: `bmw_before` and `bmw_after`; each appears only on this route.

### `/ceny`

- H1: `Цены на услуги`.
- Left category navigation, central filterable service table, right consultant.
- Diagnostics rows include 990, 1,990, and 4,900 ruble services with duration.
- Bottom continuation: fixed-price policy, current offers, parts, warranty.
- Photo roles: `mechanic_portrait` and `engine_inspection`; each appears only on
  this route.

## Allowed Above-The-Fold Copy

- `ТОЧКА ХОДА`, `АВТОСЕРВИС`
- `Услуги`, `Цены`, `Акции`, `О сервисе`, `Портфолио`, `Контакты`
- `+7 (495) 128-95-95`, `Ежедневно с 9:00 до 21:00`, `Записаться`
- Route-specific headings and factual labels listed above.

Do not invent hero kickers, promotional badges, awards, fake ratings, or
additional navigation items.

## Fidelity Gate

For every rendered route compare at original resolution:

1. header anatomy and navigation order;
2. route title, hierarchy, and above-the-fold copy;
3. true-white/red/black palette with no overlays;
4. layout and container model;
5. unique photo role and crop;
6. lower-band meaningful content;
7. exact semantic URL in browser chrome.

