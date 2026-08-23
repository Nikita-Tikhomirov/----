# Premium Kwork Portfolio Redesign

## Purpose

Replace the deleted low-quality portfolio pack with 15 convincing Russian-language website projects that present the developer as a premium web specialist. Every work must look like a distinct, commissioned, production-ready product rather than a recolored template or a generated moodboard.

## Failure Audit

The previous pack failed because the implementation diverged from its strongest visual concepts:

- 15 projects were reduced to three shared renderer families and common page structures.
- Each project declared only one `hero.png`, then reused it across cover, content, function, and mobile frames.
- Every project was forced into the same `cover/content/function/mobile` shot sequence.
- Large blank areas, sparse content, repeated navigation patterns, and generic cards made the sites look unfinished.
- Validation checked dimensions, file size, and nonblank pixels, but did not check concept fidelity, asset reuse, visual density, or cross-project similarity.
- The generated full-page concepts were treated as disposable inspiration instead of authoritative visual specifications.

No previous screenshot or generated hero asset may be uploaded again.

## Deliverable

- Exactly 15 separate Kwork portfolio works.
- Exactly five 1920x1280 PNG screenshots per work.
- All five screenshots are desktop browser views. Mobile screenshots are excluded from this pack.
- Each work has its own brand, meaningful `.ru` domain, visual system, site architecture, copy, data, and interactive states.
- Each work is identified in Kwork metadata as an author concept, while the screenshots themselves look like a real operating website.

## Project Groups

### Premium services and commerce

1. `tochka-hoda.ru` - automotive service and online booking.
2. `dentalea-clinic.ru` - private dental clinic and doctor scheduling.
3. `ventkontur.ru` - engineering ventilation catalog and equipment selection.
4. `syr-hleb.ru` - gourmet food store and gift-box builder.
5. `kvadrat-remonta.ru` - residential renovation studio and project estimate.

### Lead-generation businesses

6. `okna-sfera.ru` - windows, measurement, and configuration.
7. `chistiy-metr.ru` - premium cleaning and room-by-room estimate.
8. `teplodom-service.ru` - boiler diagnostics and emergency service.
9. `berezhny-pereezd.ru` - moving service and route calculator.
10. `pravovaya-opora.ru` - legal practice and case assessment.

### Product and operational systems

11. `severniy-marshrut.ru` - outdoor equipment ecommerce.
12. `modulprof.ru` - modular building configurator and B2B catalog.
13. `doma-u-ozera.ru` - holiday-home booking service.
14. `praktika-navyka.ru` - education platform with learner workspace.
15. `gruzcontrol.ru` - logistics operations dashboard.

## Five-Screen Story Per Work

Each project defines five routes that tell a coherent product story. Route names vary by product and may not be generic aliases shared across all projects.

1. Homepage or primary workspace: a convincing first viewport and visible continuation below it.
2. Detailed inner page: service, category, property, course, project, or equipment detail.
3. Functional state: booking, calculator, cart, configurator, assessment, scheduler, or operations workflow.
4. Proof or decision page: case study, comparison, reviews, pricing, technical documentation, or analytics detail.
5. Secondary real-world state: search results, order summary, profile, team, project gallery, or status detail.

## Visual Standard

- The first screenshot of every work is a desktop cover, never a mobile device mockup.
- The website fills the browser viewport. The lower 25% may not be an empty white field.
- Brand/product/place is visible in the first viewport and the next section is visibly beginning.
- Layouts must use domain-appropriate density. Operational tools are compact; service and commerce sites are content-rich and sales-focused.
- Each project has a distinct art direction: grid, typography, color, image treatment, navigation, controls, and motion/state language.
- Shared code is limited to browser chrome, safe HTML escaping, icons, and screenshot orchestration. Site headers, heroes, cards, sections, and page layouts are project-owned.
- Typography must be deliberate and legible. No viewport-scaled fonts, negative letter spacing, or oversized panel headings.
- Text must be natural Russian copy with plausible names, addresses, prices, dates, specifications, reviews, and legal/support details.
- Screens may include realistic browser chrome and semantic paths such as `/uslugi/diagnostika`, `/catalog/vku-4500`, or `/booking/dom-lesnoy`.

## Original Asset Contract

- Every project declares at least six production bitmap assets with semantic keys.
- No photographic bitmap may be reused between two screenshots, even within one project.
- No bitmap may be reused across projects.
- Every bitmap is generated specifically for its project and inspected at original resolution.
- Generated bitmaps contain no required interface text. All interface text remains code-native.
- Logos, diagrams, maps, tables, icons, and UI states are rendered in HTML/CSS where exactness matters.
- Asset SHA-256 and perceptual hashes must be unique across the complete pack.

## Flagship Gate

`tochka-hoda` is the mandatory flagship and quality gate. Its five screens are:

1. `/` - premium homepage matching or exceeding the approved red/white automotive concept.
2. `/uslugi/diagnostika-avtomobilya` - detailed diagnostic service with packages and included checks.
3. `/zapis/diagnostika` - booking workflow with vehicle, date, time, and selected package.
4. `/raboty/bmw-x5-hodovaya` - photographic case study with findings, work list, and result.
5. `/ceny` - filterable service price catalog with offers and trust details.

The remaining 14 projects may not be rendered until the flagship passes all automated checks and a manual original-resolution review of all five screenshots.

## Automated Quality Gates

- Exactly 15 projects, five shots each, and 75 final PNG files.
- Every PNG is 1920x1280, valid, under 10 MB, and visually nonblank.
- No shot uses `layout="mobile"`.
- Every project owns a dedicated renderer module and route map.
- Every project has at least six declared bitmap assets.
- Asset SHA-256 values are all distinct.
- Asset perceptual hashes must exceed the configured minimum Hamming distance.
- Final screenshot perceptual hashes must reject near-identical cross-project layouts.
- The bottom viewport band must exceed minimum edge-density and color-variance thresholds.
- Every screenshot includes its exact domain and semantic route in browser chrome.
- Forbidden markers include `localhost`, `demo`, placeholder copy, lorem ipsum, and the developer's personal name.

## Manual Quality Gates

- Inspect every bitmap asset at original resolution before rendering.
- Inspect every final screenshot at original resolution after rendering.
- Compare each flagship screenshot with its visual reference side by side.
- Reject repeated photos, weak crops, malformed generated details, empty lower areas, generic card grids, implausible data, and template-like repetition.
- Record one explicit pass/fail note for content, composition, typography, asset quality, realism, URL, and uniqueness for every screenshot.
- Upload only after all 75 screenshots pass and no work is marked provisional.

## Publication Safety

- Existing user-authored Kwork portfolio works must not be modified or deleted.
- New work is uploaded only from the final manifest.
- Each Kwork work receives the five screenshots in declared order.
- After upload, reopen every Kwork work and verify title plus server-side image count before considering publication complete.
