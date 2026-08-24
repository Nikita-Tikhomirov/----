# Task 7: Product And Operational System Inventories

## Scope

This is the binding visual, content, asset, and interaction inventory for the
five product systems registered in `portfolio/kwork_pack/catalog.py`:
`sever-market`, `modulprof`, `doma-u-ozera`, `praktika`, and `gruzcontrol`.
Each system has five desktop routes and six project-owned bitmap assets. Every
asset is used exactly once on its assigned route; operational maps, charts,
plans, diagrams, and status indicators remain code-native.

## Северный маршрут

**Catalog slug:** `sever-market`
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\severniy-marshrut-concept.png`

- **Brand signal:** angular mountain mark, two-line `СЕВЕРНЫЙ МАРШРУТ`, and
  immediate catalog/search/cart utility. It must read as a serious Russian
  outdoor retailer, not an expedition landing page.
- **Palette:** snow `#FFFFFF`, pine `#173F32`, signal red `#E83B3B`, ink
  `#172027`, trail gray `#EEF1EF`, moss `#61776D`, amber rating `#F2A51A`.
- **Typography and density:** compact retail sans; strong product names,
  tabular prices and stock counts; important text is at least 12px. Catalog
  pages intentionally expose filters, comparison facts, stock, and delivery.
- **Container model:** two-level retail header, open filter rail, square product
  cells, ruled specifications, cart table, and delivery matrix. No floating
  marketing cards or decorative gradients.
- **Route anatomy:**
  - **cover** `/`: product-first expedition hero, seasonal kit selector, live
    kit price/stock, service assurances, and lower category assortment.
  - **catalog** `/catalog/turisticheskoe-snaryazhenie`: category/season/weight
    filters, sort control, result count, dense product matrix, stock by city,
    and lower expert selection strip.
  - **tents** `/catalog/palatki`: capacity/weather filters, tent comparison
    rows, selected specification, add-to-cart result, and lower field guide.
  - **cart** `/korzina`: line-item quantities, stock reservation, promo input,
    delivery mode, reconciled subtotal/discount/delivery/total, and next step.
  - **delivery** `/dostavka`: city, carrier and pickup controls, dependent cost
    and arrival window, regional coverage table, and expedition packing note.
- **Route-owned assets:** `mountain_tent` cover; `hiking_backpack` catalog;
  `gear_closeup` tents; `campfire_scene` cart; `guide_portrait` and
  `winter_route` delivery.
- **Semantic workflows:** season selector updates the cover kit, price and
  availability; catalog filters update visible result facts; tent controls
  update comparison and cart state; cart quantity/delivery mode reconcile all
  totals; city/carrier controls update delivery cost, date and route.
- **Banned patterns:** fashion marketplace styling, lifestyle-only hero,
  rounded product-card wall, fake product logos baked into photos, gradients,
  duplicate product images, or a cart that does not reconcile.

## МодульПроф

**Catalog slug:** `modulprof`
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\modulprof-concept.png`

- **Brand signal:** industrial `МодульПроф`, orange engineering accent, and
  direct access to projects, configurator, catalog and documentation.
- **Palette:** graphite `#20262B`, steel `#E9ECEE`, white `#FFFFFF`, engineering
  orange `#FF6A1A`, blueprint blue `#1872C9`, muted metal `#69747C`.
- **Typography and density:** pragmatic technical sans, aligned dimensions,
  areas, quantities and prices. Headings are compact; tables remain readable
  at 12-14px.
- **Container model:** dark utility header, hard-edged photography, technical
  tabs, specification tables, configurator worksheet, comparison columns and
  project ledger. No consumer SaaS cards or decorative 3D mockup frame.
- **Route anatomy:**
  - **cover** `/`: current building solution, purpose selector, live base
    dimensions/price/production term, engineering proof, and lower product
    families.
  - **catalog** `/catalog/modulnye-zdaniya`: purpose/area/readiness filters,
    compact building rows, delivery geography, selected model specification,
    and lower procurement conditions.
  - **configurator** `/konfigurator`: purpose, dimensions, floor, shell,
    engineering systems and delivery controls; live area, composition, term,
    weight and reconciled price; lower specification breakdown.
  - **comparison** `/sravnenie-komplektatsiy`: three packages with explicit
    included/excluded rows, active package, dependent total and lead time, and
    lower standards/documentation strip.
  - **projects** `/proekty`: industry/region filters, project ledger, selected
    installation facts, responsible architect and lower production timeline.
- **Route-owned assets:** `modular_building` cover; `factory_assembly` catalog;
  `interior_module` and `facade_detail` configurator; `architect_portrait`
  comparison; `site_installation` projects.
- **Semantic workflows:** selectors update the cover offer; catalog filters
  update count/model detail; every configurator input changes dependent
  specification or price; package selection updates the full comparison result;
  project filters update ledger totals and selected case.
- **Banned patterns:** architecture portfolio hero with no data, orange gradient,
  decorative wireframe, unreadable blueprint text, rounded SaaS cards, or a
  configurator whose price is detached from its options.

## Дома у озера

**Catalog slug:** `doma-u-ozera`
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\doma-u-ozera-concept.png`

- **Brand signal:** restrained lake/forest mark, `Дома у озера`, live date and
  guest search, and an explicit direct-booking promise. It must read as a real
  hospitality booking service, not a property-development catalog.
- **Palette:** white `#FFFFFF`, lake green `#0D513E`, berry `#B83D4B`, water
  blue `#DCECF1`, pine ink `#17312A`, quiet stone `#EFF1ED`, gold `#C99A48`.
- **Typography and density:** warm but operational sans with a restrained serif
  only for house names and principal prices. Booking facts and availability
  remain compact and unambiguous.
- **Container model:** broad unfiltered property photography, straight booking
  panels, availability calendar, amenity rows, price breakdown and policies.
  Property cards are limited to repeated search results.
- **Route anatomy:**
  - **cover** `/`: lake-house signal, date/guest search, dependent available
    house and total, direct-booking benefits, and lower house assortment.
  - **sauna-house** `/booking/dom-s-saunoy`: gallery evidence, sleeping/sauna
    capacity, amenities, selectable package, price and lower house rules.
  - **search** `/poisk-domov`: dates, guests, bedrooms, sauna/pet filters,
    dependent result count and house rows with full nightly totals.
  - **calendar** `/svobodnye-daty`: month grid with statuses and minimum stays,
    selected range, chosen house, dependent nights/price, and lower demand note.
  - **booking** `/bronirovanie`: guest/contact form, selectable extras, consent,
    exact stay/house summary, reconciled deposit/total, host contact and policy.
- **Route-owned assets:** `lakeside_house` cover; `sauna_interior` and
  `terrace_view` sauna-house; `bedroom_detail` search; `evening_pier` calendar;
  `host_portrait` booking.
- **Semantic workflows:** cover search updates availability and total; house
  package updates occupancy and price; search controls update count/results;
  calendar date selection updates nights and total; booking extras and guests
  update summary and deposit without layout shift.
- **Banned patterns:** real-estate sales copy, dark photo overlays, Airbnb clone,
  floating glass booking card, fake map screenshot, rounded card mosaic,
  ambiguous nightly versus stay price, or inert calendar dates.

## Практика

**Catalog slug:** `praktika`
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\praktika-navyka-concept.png`

- **Brand signal:** concise `Практика` wordmark with green activity dot,
  authenticated learner identity, course navigation and current progress.
- **Palette:** black `#111211`, white `#FFFFFF`, action coral `#F35E4E`,
  progress green `#149447`, turquoise `#20A6A0`, paper `#F4F5F3`, muted
  graphite `#66706B`. No purple LMS palette.
- **Typography and density:** neutral learning-product sans; readable lesson
  prose, dense curriculum rows, visible progress and due dates; minimum 12px.
- **Container model:** black account header, open workspace columns, curriculum
  tree, lesson canvas, feedback rail, progress table and assignment checklist.
  Cards are reserved for repeated courses only.
- **Route anatomy:**
  - **cover** `/`: learner dashboard signal, continue-learning state, weekly
    plan selector, dependent next lesson/deadline, mentor activity, lower path.
  - **courses** `/cabinet/courses`: active/completed filters, progress rows,
    workload selector, next action and lower upcoming reviews.
  - **curriculum** `/courses/web-design/program`: module tree, workload mode,
    dependent completion forecast, skills/outcomes and lower project milestones.
  - **lesson** `/courses/web-design/lesson-4`: lesson navigation, media stage,
    transcript/material tabs, assignment checklist, mentor feedback, and
    dependent completion state.
  - **progress** `/cabinet/progress`: period and competency filters, progress
    ledger, target selector, dependent forecast and lower mentor review history.
- **Route-owned assets:** `student_workspace` cover; `design_board` courses;
  `lesson_notebook` curriculum; `mentor_portrait` and `team_review` lesson;
  `graduation_scene` progress.
- **Semantic workflows:** weekly plan updates next action/deadline; course filter
  and workload controls update counts; curriculum pace updates forecast;
  lesson tabs/checklist update content and completion state; progress period and
  target update metrics and forecast.
- **Banned patterns:** marketing course landing page, giant video-only frame,
  purple-blue dashboard, motivational quote cards, tiny lesson copy, gradients,
  inert checklists, or progress values unrelated to controls.

## ГрузКонтроль

**Catalog slug:** `gruzcontrol`
**Reference:** `C:\Users\user\Desktop\Грут\artifacts\kwork-portfolio\concepts\gruzcontrol-concept.png`

- **Brand signal:** persistent dark operations rail, `ГрузКонтроль`, current
  Moscow time, dispatcher identity, deliveries table and explicit exception
  counts. This is a work surface, not a logistics marketing site.
- **Palette:** rail navy `#102333`, work white `#FFFFFF`, action blue `#1670D2`,
  success green `#189447`, warning amber `#F2A51A`, incident red `#E33F46`,
  canvas gray `#EEF1F3`, ink `#24313A`.
- **Typography and density:** compact system sans with tabular identifiers,
  times, weights and SLAs. Status uses color plus text, never color alone.
- **Container model:** fixed navigation rail, toolbar, KPI strip, dense tables,
  selection drawer, dispatch board, route checkpoint ledger and charts. No
  marketing hero, decorative card wall, or oversized headline.
- **Route anatomy:**
  - **cover** `/`: live operations overview with KPI strip, exception queue,
    active-delivery table, selected terminal status and lower shift handoff.
  - **deliveries** `/dashboard/dostavki`: date/service/status/search filters,
    sortable delivery table, selected detail drawer, documents and actions.
  - **dispatch** `/dashboard/dispatch`: unassigned jobs, vehicle/driver capacity,
    semantic assignment controls, live load/SLA summary and incident queue.
  - **route** `/deliveries/GC-1842`: code-native route path, driver photo,
    selectable checkpoint states, ETA/status update, cargo/documents and history.
  - **analytics** `/dashboard/analytics`: period/service filters, code-native
    KPI charts, delay reasons, warehouse scan evidence and dependent comparison.
- **Route-owned assets:** `logistics_terminal` cover; `truck_fleet` deliveries;
  `dispatcher_portrait` dispatch; `delivery_driver` and `route_overview` route;
  `warehouse_scan` analytics.
- **Semantic workflows:** overview queue selection updates detail; delivery
  filters update count and drawer; dispatch selections update assigned vehicle,
  driver, capacity and SLA; route checkpoint control updates ETA/status/history;
  analytics period/service changes all displayed metrics and chart labels.
- **Banned patterns:** landing-page hero, dark-blue full-screen monochrome,
  floating glass analytics, fake map image used as the only route state, rounded
  card grid, gradients, blank chart rectangles, or status controls that only
  recolor themselves.

## Cross-Project Locks

- No Task 7 renderer imports another renderer, style sheet, header, route body,
  interaction script, or helper that would make the systems share anatomy.
- All pages render inside the shared 1920 x 1280 browser frame with an exact,
  stable 1120px application canvas. There is meaningful content in the lower
  quarter and no clipping, overlap, horizontal overflow, or text under 12px.
- Every project-owned bitmap key appears exactly once in the assigned route and
  nowhere else. No photograph, crop, person, product, building, house, learning
  scene, vehicle, warehouse, or composition is shared between projects.
- All controls are semantic and update dependent visible content with stable
  geometry. Totals reconcile, filters change result facts, and operational
  states update summaries rather than only button appearance.
- No gradients, translucent overlays, baked-in interface text, mobile mockups,
  decorative SVG hero scenes, placeholder copy, generic card walls, or repeated
  route anatomy are permitted.
