# Task 6: Lead-Generation Design Inventories

## Scope

This is the binding visual and interaction inventory for Task 6. It covers the
five lead-generation projects registered in `portfolio/kwork_pack/catalog.py`:
`okna-sfera`, `chistiy-metr`, `teplodom`, `pereezd-prosto`, and `pravo-opora`.
The original concept PNGs were reviewed at original resolution. Asset names
below are exact catalog `AssetSpec.key` names; their catalog filenames are the
same kebab-case names with a `.png` extension.

Each project has five desktop routes. Its six declared assets must be used once
only, on the stated route. No asset may appear on another route or project.

## Окна Сфера

**Catalog slug:** `okna-sfera`  
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\okna-sfera-concept.png`

- **Brand signal:** `Окна Сфера` in a confident geometric sans, circular blue
  aperture mark, and the restrained descriptor `Качество в каждой детали`.
  The first viewport reads as a window manufacturer, not a generic home-service
  landing page.
- **Palette:** window white `#FFFFFF`; clear sky `#1D7FD1`; deep frame blue
  `#0B4F88`; calculation amber `#F7B500`; charcoal `#171B21`; mist glass
  `#EAF5FD`; muted steel `#697784`. Blue is structural, amber is reserved for
  price, active configuration, and primary conversion.
- **Typography:** modern system grotesk with a heavy, large product headline;
  compact 13-15px sans for measurements, specifications, and form labels.
  Numerical price/term values are tabular and visibly stronger than supporting
  text. Important text is never below 12px.
- **Container model:** narrow utility header plus full primary navigation;
  open white and pale-glass bands, straight 1px borders, wide comparison tables,
  and a fixed-width calculation panel. Only repeated profile/options and review
  items may be cards; page sections must remain open bands.
- **Hero treatment:** bright daylight interior with an unfiltered installer or
  window scene. Copy occupies the quiet white side; configuration sits in a
  solid white panel with no tint, blur, gradient, or photographic overlay.
- **Route-specific anatomy:**
  - **cover** `/`: split manufacturer hero, window-type selector and quote
    panel, production/installation guarantees, review source strip, then a
    full-width quality/proof band.
  - **windows** `/plastikovye-okna`: filter rail for room/window type,
    comparison table for standard window configurations, a specification
    sidebar, and a lower thermal/noise comparison band.
  - **calculator** `/raschet-okna`: stepper for opening type, dimensions,
    profile, glazing, and installation; a live price/term summary must stay
    visible beside the controls; lower band shows the selected configuration
    and what is included.
  - **profiles** `/profili`: engineering detail heading, profile chamber/
    glazing characteristics, comparison rows for warm/cold/noise performance,
    and a lower material/passport detail band.
  - **installation** `/montazh`: installation sequence, appointment slot,
    installation-day checklist, and a final handover/guarantee strip.
- **Route signatures:** configuration-first quote flow; explicit sash-type
  controls; dimension and profile-dependent price; heat/noise table; concrete
  installation handover checklist.
- **Route-owned assets:** `installer_portrait` cover; `window_facade` windows;
  `bright_kitchen` calculator; `profile_closeup` profiles; `glazing_process`
  and `balcony_view` installation.
- **Semantic interactive workflows:** sash buttons update active state,
  dimensions, base price, lead time, and product summary; calculator selects
  profile and glazing with dependent thermal/noise figures; installation date
  and time selectors update the visit summary. Use native inputs, labelled
  controls, buttons with `aria-pressed`, and a real summary region.
- **Lower viewport:** production facts, selected window specification, profile
  performance table, or installation handover conditions must reach the bottom
  of every route.
- **Banned template patterns:** blue SaaS dashboard chrome; floating translucent
  quote card over the photo; fake plastic-window icons instead of clear form
  controls; generic construction-worker testimonials; rounded card mosaics;
  gradients and stocky lifestyle hero crops.

## Чистый метр

**Catalog slug:** `chistiy-metr`  
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\chistiy-metr-concept.png`

- **Brand signal:** `Чистый метр` wordmark with a simple mint cleaning mark and
  `клининговая служба`. The first viewport communicates post-renovation
  cleaning, a transparent per-square-metre rate, and an available crew.
- **Palette:** clean white `#FFFFFF`; mint `#48C78E`; deep teal-black
  `#173F3B`; conversion coral `#F35D50`; fresh pale mint `#EAF8F1`; warm
  floor gray `#F1F3F1`; slate `#58645F`. Mint proves cleanliness; coral is only
  for booking/action states.
- **Typography:** approachable neutral grotesk; strong black price headline;
  compact sentence-case labels; generous but not editorial line-height.
  Checklist and calculator values use 12-14px high-legibility sans.
- **Container model:** white service surface, close-cropped real cleaning
  photography, transparent calculator worksheet, checklist rows, and horizontal
  fact strips. Before/after is a framed evidence pair, not a carousel card.
- **Hero treatment:** bright finished apartment with staff actively cleaning;
  no darkening, no gradient, no text placed over busy photographic detail. The
  calculator is a solid light panel against the open copy side.
- **Route-specific anatomy:**
  - **cover** `/`: service promise and rate, area/service calculator, crew
    availability, guarantee note, then a post-renovation scope/proof band.
  - **after-renovation** `/uborka-posle-remonta`: project condition header,
    explicit before/after evidence, task sequence, duration/crew estimate, and
    lower quality-control handoff.
  - **calculator** `/raschet-uborki`: area, room type, urgency, and add-on
    selectors; live total, work duration, crew, and next available window;
    lower band enumerates the chosen scope and exclusions.
  - **checklist** `/chto-vhodit`: room-zone navigation, dense checklist with
    included/excluded work, chemistry/equipment note, and lower acceptance
    checklist.
  - **reviews** `/otzyvy`: verified review ledger with service, area, date, and
    result; crew profile/availability; lower reputation metrics and guarantee
    process.
- **Route signatures:** cleaning-price calculator; real before/after evidence;
  room-zone checklist; available-crew promise; acceptance after service.
- **Route-owned assets:** `clean_kitchen` cover; `before_cleanup` and
  `after_cleanup` after-renovation; `equipment_case` calculator;
  `bathroom_detail` checklist; `cleaner_portrait` reviews.
- **Semantic interactive workflows:** area range/input, service type, urgency,
  and extras update total, duration, team size, and availability; zone controls
  update checklist count and scope summary; review filters update the visible
  review ledger and rating total. Use actual inputs, checkbox/segmented controls
  and live summary text.
- **Lower viewport:** proof of work, selected scope, acceptance actions, or
  verified review metrics must fill the lower quarter of each route.
- **Banned template patterns:** sterile all-white card dashboard; turquoise
  medical-clinic styling; animated split-slider as the only before/after proof;
  bubbly rounded chips; generic sparkle decorations; cleaning staff used as
  detached decorative portraits; gradients/overlays.

## ТеплоДом

**Catalog slug:** `teplodom`  
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\teplodom-service-concept.png`

- **Brand signal:** `ТеплоДом` with an orange roof/flame and blue heat-wave
  mark, plus the clear service descriptor `Ремонт газовых котлов`. The primary
  signal is urgent but competent home boiler repair.
- **Palette:** service navy `#0B4C8C`; emergency orange `#F47A20`; safety green
  `#16833C`; furnace charcoal `#1D252C`; porcelain `#F7F7F4`; warm sand
  `#F2E7D9`; muted graphite `#5E6870`. Orange signals urgency, navy carries
  commands and service structure, green only proves safety/availability.
- **Typography:** pragmatic bold grotesk for emergency statements and response
  times; dense 12-14px technical labels; no decorative display font. Device
  names, diagnostic codes, and price values use aligned technical numerals.
- **Container model:** white left content plane, hard-edged service photography,
  dark charcoal request sheet, logo/brand support row, and low technical rows.
  Repeated fault types may be individual compact cards; service sections are
  otherwise open bands and ruled lists.
- **Hero treatment:** a technician actively diagnosing a real boiler; the
  booking form occupies a solid charcoal side panel. It must not use a blue or
  orange image overlay, a hero gradient, or an abstract flame illustration.
- **Route-specific anatomy:**
  - **cover** `/`: urgent dispatch promise, safety/diagnostic/time proof,
    manufacturer support row, request form with time interval, and fault-type
    strip below.
  - **boiler-repair** `/remont-gazovyh-kotlov`: boiler-brand/service selector,
    fault matrix, repair stages, parts/guarantee line, and lower price/SLA
    detail.
  - **diagnostics** `/diagnostika-kotla`: symptom choices, diagnostic sequence,
    expected fixed diagnostic fee, fault-code result sheet, and lower safety
    decision band.
  - **prices** `/ceny`: transparent service/parts matrix, brand conditions,
    visit/diagnostic fee distinction, and lower warranty/payment conditions.
  - **request** `/vyzov-mastera`: address, brand, urgency, and time selector;
    assigned-master/arrival summary, consent, and lower dispatch confirmation.
- **Route signatures:** same-day dispatch; fault/brand diagnostic selector;
  technical fault-code sheet; safety confirmation; appointment window tied to
  master arrival.
- **Route-owned assets:** `repair_process` cover; `boiler_room` boiler-repair;
  `diagnostic_tool` diagnostics; `burner_closeup` prices;
  `technician_portrait` and `warm_home` request.
- **Semantic interactive workflows:** symptom and boiler-brand controls update
  expected diagnostic path/fee; urgency and time buttons update master ETA and
  dispatch summary; service rows update price/parts inclusion. Forms require
  proper labels, native inputs/selects, consent, and live confirmation copy.
- **Lower viewport:** manufacturer compatibility, fault detail, transparent
  cost/warranty terms, or dispatch confirmation is always fully visible.
- **Banned template patterns:** alarmist red-only emergency interface; an
  automotive-service visual vocabulary; full-screen dark page; fake diagnostic
  gauges; boiler-flame gradient backgrounds; rounded card walls; repeated
  technician photo across routes.

## Бережный переезд

**Catalog slug:** `pereezd-prosto`  
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\berezhny-pereezd-concept.png`

- **Brand signal:** two-line `Бережный переезд` mark, folded-box/house icon,
  cobalt first line and orange second line. The first viewport promises a
  calm, protected apartment move with a concrete quote and loading slot.
- **Palette:** moving blue `#1768CF`; deep navy `#17345E`; packing orange
  `#FF7A18`; warm carton `#F4E6D6`; white `#FFFFFF`; blue mist `#EEF5FD`; ink
  `#202833`. Orange marks cost/action; cobalt drives route and status states.
- **Typography:** direct bold grotesk for the mover promise and price; compact
  utility sans for inventory, floors, times, route details, and status. Avoid
  tech-dashboard or luxury editorial typography.
- **Container model:** broad home/move photography, operational quote sheet,
  two-column origin/destination detail, straight route/timeline lines, and
  proof bands. Repeated package choices may be cards; the move process should
  be an unframed horizontal sequence.
- **Hero treatment:** a genuinely active moving team with wrapped furniture,
  labelled cartons, and vehicle context. The quote tool is a solid white
  functional panel; do not darken or blur the moving photo for readability.
- **Route-specific anatomy:**
  - **cover** `/`: apartment-moving promise, room/volume mode, basic quote
    summary, route/date detail, arrival window, and lower five-step process.
  - **apartment-moving** `/kvartirnyy-pereezd`: package/service scope, room
    inventory, crew/vehicle specification, insurance terms, and lower move-day
    timeline.
  - **calculator** `/raschet-pereezda`: rooms or volume toggle, floors/lift,
    packing, route, and date controls; live price, crew, vehicle, duration, and
    loading slot; lower estimate breakdown.
  - **packing** `/upakovka-veshchey`: material quantities, fragile-item choices,
    packing sequence, inventory label example, and lower responsibility/claim
    terms.
  - **route** `/marshrut`: origin/destination route worksheet, parking/elevator
    checkpoints, vehicle assignment, route timing, and lower confirmation
    timeline to the new home.
- **Route signatures:** rooms-versus-volume estimator; origin/destination
  routing; floor/lift-dependent price; packing inventory; five-step move
  handoff.
- **Route-owned assets:** `moving_van` cover; `packed_living_room`
  apartment-moving; `boxes_detail` calculator; `packer_portrait` packing;
  `route_map_photo` and `new_home` route.
- **Semantic interactive workflows:** room/volume mode, room count, floors,
  lift, packing, and date update price, crew, truck, duration, and loading
  window; route checkpoint selections update distance/parking summary; packing
  choices update materials/inventory count. Controls are labelled segmented
  buttons, steppers, inputs, and checkboxes with a visible dependent summary.
- **Lower viewport:** exact estimate components, packing responsibility,
  vehicle/route confirmation, or the complete move handoff must fill the lower
  band.
- **Banned template patterns:** travel-booking UI; airport/map SaaS styling;
  generic cardboard-box illustrations; oversize blue gradients; floating glass
  quote cards; random customer portrait grids; reusing a single mover photo on
  more than one route.

## Правовая опора

**Catalog slug:** `pravo-opora`  
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\pravovaya-opora-concept.png`

- **Brand signal:** shield monogram, high-contrast serif `ПРАВОВАЯ ОПОРА`, and
  small `ЮРИДИЧЕСКОЕ БЮРО` descriptor. It must feel confidential, sober, and
  consumer-rights-focused rather than corporate-finance or medical.
- **Palette:** legal forest `#173F37`; old gold `#D5AE58`; ink `#232428`;
  paper ivory `#F7F2E9`; oxblood `#7A3035`; quiet gray `#73746F`; white
  `#FFFFFF`. Forest conveys trust, gold is reserved for primary decisions and
  proof, and oxblood appears only for risk/claim states.
- **Typography:** high-contrast serif for principal headlines, amounts, and
  case outcomes; disciplined sans for controls, dates, court stages, and form
  labels. Avoid decorative calligraphy, tiny legal-print text, or more than two
  type families. Important text is at least 12px.
- **Container model:** open ivory/white editorial sheets, framed evidence
  documents, calm ruled case tables, dark forest consultation module, and a
  formal result strip. Only repeated court cases or service options may be
  modest cards; no nested card construction.
- **Hero treatment:** a real lawyer-client consultation in a bright office.
  Headline and consultation action live on the quiet open side; no artificial
  courtroom backdrop, heavy black gradient, or legal-symbol stock overlay.
- **Route-specific anatomy:**
  - **cover** `/`: consumer-rights promise, one-minute assessment entry,
    confidentiality proof, legal outcomes strip, and lower four-step work
    sequence.
  - **developer-disputes** `/uslugi/spory-s-zastroyshchikom`: claim scenarios,
    developer/document deadline matrix, likely evidence list, cost/recovery
    outline, and lower filing sequence.
  - **assessment** `/otsenka-dela`: five-question case assessment with issue,
    contract, deadline, and desired outcome; live legal-path/risk summary and
    lower document-preparation checklist.
  - **practice** `/sudebnaya-praktika`: outcome ledger with claim, recovered
    amount, court stage, term, and anonymised evidence; lower court-process
    timeline and scope note.
  - **consultation** `/konsultatsiya`: specialist/time selector, case summary,
    secure document upload placeholder, consent, and lower confirmation with
    preparation list.
- **Route signatures:** one-minute legal assessment; claim/deadline matrix;
  recovered-amount practice ledger; confidentiality/status proof; consultation
  schedule linked to the submitted case summary.
- **Route-owned assets:** `consultation_table` cover; `office_exterior`
  developer-disputes; `case_documents` assessment; `courtroom_hall` practice;
  `lawyer_portrait` and `client_meeting` consultation.
- **Semantic interactive workflows:** five assessment answers update issue
  classification, deadline flag, preparation list, and recommended next step;
  practice filters update outcomes and aggregate recovered amount; consultation
  specialist/time controls update the lawyer, meeting format, and case summary.
  Use labelled radio groups, native form elements, disclosure-safe placeholder
  fields, consent, and semantic status text.
- **Lower viewport:** confidential process summary, document checklist, court
  timeline, or consultation preparation/confirmation must complete every route
  inside the desktop frame.
- **Banned template patterns:** generic blue law-firm site; gavels, scales, or
  courthouse illustrations used as decoration; frightening red claim banners;
  cryptocurrency/finance dashboard tables; pseudo-handwritten serif type;
  gold-gradient luxury effects; testimonial-card carousels.

## Cross-Project Locks

- Render each project as a separate site with its own header anatomy, content
  density, palette, type hierarchy, conversion control placement, and lower
  band. Do not import or copy renderer helpers, CSS, header structures, hero
  compositions, route bodies, or interaction scripts between any Task 6 project
  or from the five commercial sites.
- Every bitmap key declared for a project appears exactly once in its own five
  routes, only on the route stated above. One two-asset route is allowed only
  where stated. No photo, crop, person, tool, room, vehicle, court scene,
  cleaning scene, or composition is shared between projects.
- All final pages use the shared 1920 x 1280 browser frame, retain a stable
  1120px page canvas, use meaningful lower-quarter content, and have no
  clipping, overlaps, blank terminal bands, or text under 12px.
- Interactions must be real semantic controls with dependent visible content in
  a real browser: selected state, computed/updated result, and stable geometry
  are mandatory.
- No gradients, translucent overlays, fake text baked into images, mobile
  mockups, unrelated template screenshots, decorative SVG hero scenes, rounded
  card walls, generic landing-page testimonial blocks, placeholder copy, or
  repeated route anatomy.
