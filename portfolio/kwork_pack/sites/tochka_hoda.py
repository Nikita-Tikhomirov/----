"""Premium five-route renderer for the Tochka Hoda automotive concept."""

from collections.abc import Callable, Mapping

from ..components import escape_html
from ..icons import icon
from ..models import ProjectSpec, ShotSpec
from .runtime import RenderedPage


_ASSETS_BY_ROUTE = {
    "cover": ("workshop_hero",),
    "diagnostics": ("diagnostic_closeup",),
    "booking": ("service_lounge",),
    "case-study": ("bmw_before", "bmw_after"),
    "prices": ("mechanic_portrait", "engine_inspection"),
}

_CSS = r"""
.th-page {
  --th-red: #e50914;
  --th-red-dark: #c90710;
  --th-ink: #101114;
  --th-muted: #676b73;
  --th-line: #e0e2e6;
  --th-soft: #f5f6f7;
  width: 100%;
  height: 1120px;
  overflow: hidden;
  background: #ffffff;
  color: var(--th-ink);
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 15px;
  line-height: 1.45;
}
.th-page * { box-sizing: border-box; }
.th-page button,
.th-page input,
.th-page select { font: inherit; }
.th-page button { cursor: default; }
.th-page h1,
.th-page h2,
.th-page h3,
.th-page p { margin: 0; }
.th-header {
  display: grid;
  grid-template-columns: 282px 1fr 250px 178px;
  align-items: center;
  gap: 24px;
  height: 96px;
  padding: 0 68px;
  border-bottom: 1px solid var(--th-line);
  background: #ffffff;
}
.th-logo {
  width: max-content;
  color: #08090a;
  font-size: 30px;
  font-weight: 900;
  line-height: .82;
  text-transform: uppercase;
}
.th-logo strong { color: var(--th-red); font-size: 37px; }
.th-logo small {
  display: block;
  margin-top: 10px;
  padding-left: 52px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 5px;
}
.th-nav { display: flex; align-items: stretch; height: 96px; gap: 38px; }
.th-nav a {
  position: relative;
  display: flex;
  align-items: center;
  color: #1d1f23;
  font-size: 16px;
  text-decoration: none;
  white-space: nowrap;
}
.th-nav a.active::after {
  position: absolute;
  right: 0;
  bottom: 20px;
  left: 0;
  height: 3px;
  background: var(--th-red);
  content: "";
}
.th-phone { text-align: right; }
.th-phone strong { display: block; font-size: 19px; font-weight: 650; }
.th-phone span { display: block; margin-top: 3px; color: var(--th-muted); font-size: 13px; }
.th-primary,
.th-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 24px;
  border: 1px solid var(--th-red);
  border-radius: 4px;
  background: var(--th-red);
  color: #ffffff;
  font-weight: 700;
}
.th-secondary { background: #ffffff; color: var(--th-red); }
.th-breadcrumbs { color: #858990; font-size: 12px; }
.th-breadcrumbs span { padding: 0 10px; color: #b3b6bb; }
.th-section-title { font-size: 36px; line-height: 1.05; font-weight: 800; }
.th-lead { margin-top: 10px; color: var(--th-muted); font-size: 17px; }
.th-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--th-red);
}
.th-icon .lucide-icon { width: 28px; height: 28px; }
.th-muted { color: var(--th-muted); }

.th-home-hero {
  position: relative;
  display: grid;
  grid-template-columns: 46% 54%;
  height: 620px;
  overflow: hidden;
}
.th-home-copy {
  position: relative;
  z-index: 2;
  padding: 72px 0 0 86px;
  background: #ffffff;
}
.th-home-copy h1 {
  max-width: 700px;
  font-size: 51px;
  line-height: 1.12;
  font-weight: 830;
  text-transform: uppercase;
}
.th-home-copy > p { margin-top: 18px; color: var(--th-muted); font-size: 22px; }
.th-offer {
  display: grid;
  grid-template-columns: 102px 1fr;
  width: 610px;
  margin-top: 34px;
  padding: 18px;
  border: 1px solid #dadde1;
  border-radius: 6px;
  background: #ffffff;
}
.th-offer-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 82px;
  height: 82px;
  border-radius: 5px;
  background: var(--th-red);
  color: #ffffff;
}
.th-offer-mark .lucide-icon { width: 45px; height: 45px; }
.th-offer h2 { font-size: 21px; line-height: 1.25; }
.th-offer-actions { display: flex; align-items: center; gap: 18px; margin-top: 15px; }
.th-offer-price {
  min-width: 104px;
  padding: 7px 14px;
  border: 1px solid var(--th-line);
  border-radius: 4px;
  color: var(--th-red);
  font-size: 25px;
  font-weight: 800;
}
.th-offer-note { grid-column: 1 / -1; margin-top: 15px; color: #979ba2; font-size: 13px; }
.th-home-photo { position: relative; overflow: hidden; background: #f2f3f4; }
.th-home-photo::before {
  position: absolute;
  z-index: 1;
  top: 0;
  bottom: 0;
  left: 0;
  width: 90px;
  background: linear-gradient(90deg, #ffffff, rgba(255,255,255,0));
  content: "";
}
.th-home-photo img { width: 100%; height: 100%; object-fit: cover; object-position: 54% center; }
.th-trust-row {
  position: absolute;
  z-index: 3;
  right: 60px;
  bottom: 28px;
  left: 76px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
  padding: 17px 20px;
  background: rgba(255,255,255,.95);
  border: 1px solid #eceef0;
}
.th-trust-item { display: grid; grid-template-columns: 42px 1fr; gap: 10px; align-items: center; }
.th-trust-item strong { display: block; font-size: 14px; }
.th-trust-item span { color: var(--th-muted); font-size: 12px; }
.th-home-services { height: 404px; padding: 33px 78px 26px; border-top: 1px solid #eceef0; }
.th-home-services-head { text-align: center; }
.th-home-services-head span { color: var(--th-red); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.th-home-services-head h2 { margin-top: 7px; font-size: 30px; text-transform: uppercase; }
.th-service-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 34px; margin-top: 27px; }
.th-service-item { min-height: 180px; padding-top: 19px; border-top: 3px solid var(--th-red); }
.th-service-item h3 { font-size: 17px; line-height: 1.25; }
.th-service-item p { margin-top: 18px; color: var(--th-muted); font-size: 13px; line-height: 1.55; }
.th-services-link { display: flex; justify-content: center; margin-top: 20px; }

.th-diagnostic-top {
  display: grid;
  grid-template-columns: 46% 54%;
  height: 500px;
  overflow: hidden;
}
.th-diagnostic-copy { padding: 24px 52px 22px 72px; }
.th-diagnostic-copy h1 { margin-top: 16px; font-size: 45px; line-height: 1.05; }
.th-diagnostic-price { margin-top: 10px; font-size: 18px; }
.th-diagnostic-price strong { margin-left: 8px; color: var(--th-red); font-size: 34px; }
.th-package-panel {
  display: grid;
  grid-template-columns: 42% 58%;
  height: 242px;
  margin-top: 18px;
  border: 1px solid #d9dce1;
  border-radius: 5px;
  overflow: hidden;
}
.th-package-list { border-right: 1px solid #d9dce1; }
.th-package {
  display: grid;
  grid-template-columns: 48px 1fr;
  align-items: center;
  min-height: 80px;
  padding: 11px 14px;
  border-bottom: 1px solid #e5e6e9;
  background: #ffffff;
}
.th-package:last-child { border-bottom: 0; }
.th-package.active { box-shadow: inset 3px 0 var(--th-red); background: #fffafa; }
.th-package strong { display: block; font-size: 14px; }
.th-package span { display: block; color: var(--th-muted); font-size: 11px; }
.th-package-detail { padding: 20px 24px; }
.th-check-list { display: grid; gap: 12px; }
.th-check-line { display: flex; align-items: center; gap: 10px; color: #4f535b; font-size: 13px; }
.th-check-line .lucide-icon { color: var(--th-red); }
.th-package-total {
  display: flex;
  align-items: end;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #cfd2d6;
  font-size: 12px;
}
.th-package-total strong { color: var(--th-red); font-size: 24px; }
.th-diagnostic-action { display: flex; align-items: center; gap: 18px; margin-top: 14px; }
.th-diagnostic-action span { color: var(--th-muted); font-size: 11px; }
.th-diagnostic-photo img { width: 100%; height: 100%; object-fit: cover; object-position: center; }
.th-proof-strip {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  height: 88px;
  padding: 0 58px;
  border-top: 1px solid var(--th-line);
  border-bottom: 1px solid var(--th-line);
}
.th-proof-item { display: flex; align-items: center; gap: 12px; padding: 0 16px; border-right: 1px solid var(--th-line); }
.th-proof-item:last-child { border-right: 0; }
.th-proof-item strong { display: block; font-size: 12px; }
.th-proof-item span { display: block; color: var(--th-muted); font-size: 10px; }
.th-diagnostic-checklist { height: 436px; padding: 24px 58px; }
.th-diagnostic-checklist h2 { font-size: 28px; }
.th-diagnostic-checklist > p { margin-top: 3px; color: var(--th-muted); font-size: 13px; }
.th-check-columns { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-top: 15px; }
.th-check-group { min-height: 300px; padding: 15px 18px; border: 1px solid var(--th-line); border-radius: 5px; }
.th-check-group h3 { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 10px; font-size: 14px; }
.th-check-count { display: grid; width: 25px; height: 25px; place-items: center; border: 1px solid var(--th-line); border-radius: 50%; color: var(--th-muted); font-size: 10px; font-weight: 700; }
.th-check-group ol { margin: 12px 0 0; padding-left: 20px; color: #555a62; font-size: 11px; line-height: 1.55; }

.th-booking-title { height: 96px; padding: 18px 58px 0; }
.th-booking-title h1 { margin-top: 8px; font-size: 38px; }
.th-booking-title p { color: var(--th-muted); font-size: 13px; }
.th-booking-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 395px;
  gap: 30px;
  height: 688px;
  padding: 0 58px;
}
.th-steps { display: grid; grid-template-rows: 104px 116px 214px 224px; gap: 10px; }
.th-step { display: grid; grid-template-columns: 175px 1fr; border-bottom: 1px solid var(--th-line); }
.th-step-label { display: grid; grid-template-columns: 42px 1fr; align-content: start; padding-top: 14px; }
.th-step-number { color: var(--th-red); font-size: 27px; font-weight: 800; }
.th-step-label strong { display: block; font-size: 17px; }
.th-step-label span { display: block; margin-top: 4px; color: var(--th-muted); font-size: 11px; }
.th-step-content { align-self: stretch; padding: 14px 18px; border: 1px solid var(--th-line); border-radius: 4px; }
.th-selected-row { display: flex; align-items: center; justify-content: space-between; height: 100%; }
.th-selected-main { display: flex; align-items: center; gap: 16px; }
.th-selected-main .th-icon { width: 50px; height: 50px; border-radius: 4px; background: var(--th-red); color: #ffffff; }
.th-selected-main strong { display: block; font-size: 18px; }
.th-selected-main span { color: var(--th-muted); font-size: 12px; }
.th-change { min-height: 38px; padding: 0 18px; border: 1px solid var(--th-line); border-radius: 3px; background: #ffffff; }
.th-date-layout { display: grid; grid-template-columns: 370px 1fr; height: 100%; }
.th-calendar { padding-right: 20px; border-right: 1px solid var(--th-line); }
.th-calendar-head { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; }
.th-calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-top: 8px; text-align: center; }
.th-calendar-grid span { display: flex; align-items: center; justify-content: center; height: 21px; font-size: 10px; }
.th-calendar-grid .muted { color: #b1b4b9; }
.th-calendar-grid .selected { width: 24px; margin: 0 auto; border-radius: 50%; background: var(--th-red); color: #ffffff; font-weight: 800; }
.th-time-panel { padding-left: 22px; }
.th-time-panel > strong { font-size: 12px; }
.th-time-list { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
.th-time { height: 44px; border: 1px solid var(--th-line); border-radius: 4px; background: #ffffff; font-size: 17px; }
.th-time.active { border-color: var(--th-red); color: var(--th-red); font-weight: 800; }
.th-contact-fields { display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: 12px; }
.th-field label { display: block; color: var(--th-muted); font-size: 10px; }
.th-field div { height: 38px; margin-top: 5px; padding: 9px 12px; border: 1px solid var(--th-line); border-radius: 3px; font-size: 12px; }
.th-consent { margin-top: 11px; color: var(--th-muted); font-size: 10px; }
.th-order-summary { align-self: start; padding: 18px; border: 1px solid var(--th-line); border-radius: 5px; }
.th-order-summary img { width: 100%; height: 180px; object-fit: cover; border-radius: 3px; }
.th-order-summary h2 { margin-top: 14px; font-size: 16px; }
.th-summary-list { display: grid; gap: 10px; margin-top: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--th-line); }
.th-summary-row { display: flex; justify-content: space-between; gap: 18px; font-size: 12px; }
.th-summary-row span:first-child { color: var(--th-muted); }
.th-summary-total { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; font-size: 18px; font-weight: 800; }
.th-summary-total strong { color: var(--th-red); font-size: 29px; }
.th-order-summary .th-primary { width: 100%; margin-top: 10px; }
.th-booking-bottom {
  display: grid;
  grid-template-columns: 1.8fr .65fr .65fr;
  height: 240px;
  margin: 0 18px;
  border: 1px solid var(--th-line);
}
.th-visit-flow { padding: 20px 26px; border-right: 1px solid var(--th-line); }
.th-visit-flow h2 { font-size: 18px; }
.th-flow-items { display: grid; grid-template-columns: repeat(5, 1fr); gap: 18px; margin-top: 25px; }
.th-flow-item { position: relative; padding-top: 28px; text-align: center; }
.th-flow-item::before { position: absolute; top: 8px; right: 0; left: 0; height: 1px; background: #d4d6d9; content: ""; }
.th-flow-item b { position: absolute; z-index: 1; top: -2px; left: calc(50% - 11px); display: grid; width: 22px; height: 22px; place-items: center; border-radius: 50%; background: var(--th-red); color: #ffffff; font-size: 10px; }
.th-flow-item strong { display: block; margin-top: 7px; font-size: 12px; }
.th-flow-item span { display: block; margin-top: 5px; color: var(--th-muted); font-size: 9px; }
.th-note-column { padding: 20px 22px; border-right: 1px solid var(--th-line); }
.th-note-column:last-child { border-right: 0; }
.th-note-column h3 { font-size: 14px; }
.th-note-column ul { margin: 14px 0 0; padding: 0; list-style: none; }
.th-note-column li { margin-top: 11px; padding-left: 18px; color: #656a72; font-size: 10px; }
.th-note-column li::before { float: left; margin-left: -18px; color: var(--th-red); content: "✓"; }

.th-case-hero { display: grid; grid-template-columns: 44% 56%; height: 420px; overflow: hidden; }
.th-case-copy { padding: 24px 34px 18px 70px; }
.th-case-copy h1 { margin-top: 17px; max-width: 680px; font-size: 45px; line-height: 1.08; }
.th-case-copy > p { margin-top: 15px; max-width: 600px; color: var(--th-muted); font-size: 16px; }
.th-case-metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 28px; }
.th-case-metric { min-height: 82px; padding-right: 10px; border-right: 1px solid var(--th-line); }
.th-case-metric:last-child { border-right: 0; }
.th-case-metric span { display: block; margin-top: 8px; color: var(--th-muted); font-size: 10px; }
.th-case-metric strong { display: block; margin-top: 4px; font-size: 14px; }
.th-case-hero-photo img { width: 100%; height: 100%; object-fit: cover; object-position: center; }
.th-diagnosis-strip { display: grid; grid-template-columns: 70px 1fr 1fr 1fr; align-items: center; height: 100px; margin: 0 68px; padding: 0 26px; border: 1px solid var(--th-line); }
.th-alert { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 50%; background: var(--th-red); color: #ffffff; font-size: 27px; font-weight: 800; }
.th-diagnosis-item { padding: 0 22px; }
.th-diagnosis-item strong { display: block; font-size: 12px; }
.th-diagnosis-item span { display: block; margin-top: 5px; color: var(--th-muted); font-size: 11px; }
.th-case-grid { display: grid; grid-template-columns: 1.05fr 1.05fr 1fr; gap: 16px; height: 504px; padding: 16px 68px 22px; }
.th-case-panel { padding: 16px 18px; border: 1px solid var(--th-line); border-radius: 4px; overflow: hidden; }
.th-case-panel h2 { font-size: 18px; }
.th-finding { margin-top: 12px; }
.th-finding img { width: 100%; height: 205px; object-fit: cover; object-position: center 58%; border-radius: 3px; }
.th-finding-copy { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 13px; }
.th-finding-copy section + section { padding-left: 14px; border-left: 1px solid var(--th-line); }
.th-finding h3 { font-size: 13px; line-height: 1.25; }
.th-finding p { margin-top: 6px; color: var(--th-muted); font-size: 9px; line-height: 1.45; }
.th-repair-proof { display: grid; grid-template-columns: repeat(3, 1fr); margin-top: 13px; padding-top: 11px; border-top: 1px solid var(--th-line); }
.th-repair-proof div { padding: 0 9px; border-right: 1px solid var(--th-line); }
.th-repair-proof div:first-child { padding-left: 0; }
.th-repair-proof div:last-child { border-right: 0; }
.th-repair-proof strong { display: block; color: var(--th-red); font-size: 13px; }
.th-repair-proof span { display: block; margin-top: 2px; color: var(--th-muted); font-size: 8px; }
.th-work-list { margin: 12px 0 0; padding-left: 18px; color: #50555c; font-size: 11px; line-height: 1.7; }
.th-parts { margin-top: 12px; border-top: 1px solid var(--th-line); }
.th-part { display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #eceef0; font-size: 10px; }
.th-case-total { display: flex; justify-content: space-between; margin-top: 13px; padding: 12px; border: 1px solid var(--th-red); font-weight: 800; }
.th-case-total strong { color: var(--th-red); font-size: 22px; }
.th-result-table { width: 100%; margin-top: 12px; border-collapse: collapse; font-size: 10px; }
.th-result-table th,
.th-result-table td { padding: 7px 5px; border-bottom: 1px solid var(--th-line); text-align: left; }
.th-result-table th { color: var(--th-muted); font-weight: 500; }
.th-before { color: var(--th-red); }
.th-after { color: #199252; }
.th-quote { margin-top: 15px; padding: 14px; border-left: 4px solid var(--th-red); background: #fafafa; color: #555a61; font-size: 11px; }
.th-warranty { display: flex; align-items: center; gap: 12px; margin-top: 12px; font-size: 11px; }

.th-prices-title { height: 132px; padding: 18px 68px 0; }
.th-prices-title h1 { margin-top: 10px; font-size: 42px; }
.th-prices-title p { color: var(--th-muted); font-size: 13px; }
.th-prices-main { display: grid; grid-template-columns: 285px 1fr 270px; gap: 20px; height: 590px; padding: 0 68px 18px; }
.th-category-list { border: 1px solid var(--th-line); border-radius: 4px; overflow: hidden; }
.th-category {
  display: flex;
  align-items: center;
  gap: 13px;
  height: 78px;
  padding: 0 18px;
  border-bottom: 1px solid var(--th-line);
  background: #ffffff;
  color: #555a61;
}
.th-category:last-child { border-bottom: 0; }
.th-category.active { box-shadow: inset 3px 0 var(--th-red); color: var(--th-ink); font-weight: 750; }
.th-table-panel h2 { font-size: 25px; }
.th-price-filters { display: flex; justify-content: flex-end; gap: 10px; margin: -32px 0 12px; }
.th-filter { display: flex; align-items: center; justify-content: space-between; min-width: 145px; height: 38px; padding: 0 12px; border: 1px solid var(--th-line); border-radius: 3px; background: #ffffff; font-size: 11px; }
.th-price-table { width: 100%; border-collapse: collapse; border: 1px solid var(--th-line); }
.th-price-table th { height: 38px; padding: 0 14px; background: #fafafa; color: var(--th-muted); font-size: 10px; font-weight: 500; text-align: left; }
.th-price-table td { height: 57px; padding: 7px 14px; border-top: 1px solid var(--th-line); font-size: 11px; }
.th-price-table td:first-child { width: 56%; }
.th-price-table td:first-child strong { display: block; color: var(--th-ink); font-size: 12px; }
.th-price-table td:first-child span { display: block; color: var(--th-muted); font-size: 9px; }
.th-price-value { color: var(--th-red); font-size: 19px; font-weight: 800; white-space: nowrap; }
.th-row-action { min-height: 34px; padding: 0 15px; border: 0; border-radius: 3px; background: var(--th-red); color: #ffffff; font-size: 10px; font-weight: 700; }
.th-consultant { padding: 15px; border: 1px solid var(--th-line); border-radius: 4px; }
.th-consultant h2 { font-size: 14px; }
.th-consultant img { width: 100%; height: 215px; margin-top: 10px; object-fit: cover; object-position: center 20%; }
.th-consultant h3 { margin-top: 10px; font-size: 14px; }
.th-consultant > p { color: var(--th-muted); font-size: 10px; }
.th-contact-list { display: grid; gap: 8px; margin-top: 12px; font-size: 11px; }
.th-contact-line { display: flex; align-items: center; gap: 8px; }
.th-contact-line .lucide-icon { color: var(--th-red); }
.th-consultant .th-secondary { width: 100%; min-height: 38px; margin-top: 14px; font-size: 11px; }
.th-prices-bottom {
  display: grid;
  grid-template-columns: 1.1fr 1.2fr 1fr 1fr;
  height: 302px;
  margin: 0 68px;
  border: 1px solid var(--th-line);
}
.th-bottom-panel { position: relative; padding: 18px 20px; border-right: 1px solid var(--th-line); overflow: hidden; }
.th-bottom-panel:last-child { border-right: 0; }
.th-bottom-panel h2 { font-size: 16px; }
.th-bottom-panel > p { margin-top: 8px; color: var(--th-muted); font-size: 10px; }
.th-policy-photo { position: absolute; right: 14px; bottom: 14px; width: 140px; height: 96px; object-fit: cover; border-radius: 3px; }
.th-policy-points { margin: 18px 130px 0 0; padding: 0; list-style: none; }
.th-policy-points li { margin-top: 8px; color: #555a61; font-size: 9px; }
.th-offers { margin-top: 10px; }
.th-offer-line { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--th-line); font-size: 10px; }
.th-offer-line strong:last-child { color: var(--th-red); font-size: 16px; }
.th-parts-list { margin: 14px 0 0; padding: 0; list-style: none; }
.th-parts-list li { margin-top: 9px; color: #555a61; font-size: 10px; }
.th-parts-list li::before { margin-right: 8px; color: var(--th-red); content: "✓"; }
.th-warranty-big { display: grid; grid-template-columns: 62px 1fr; gap: 12px; margin-top: 24px; }
.th-warranty-big .lucide-icon { width: 58px; height: 58px; color: var(--th-red); }
.th-warranty-big strong { display: block; font-size: 13px; }
.th-warranty-big span { display: block; margin-top: 7px; color: var(--th-muted); font-size: 10px; }
"""

_SCRIPTS = r"""
document.querySelectorAll('[data-selectable]').forEach(function (element) {
  element.addEventListener('click', function () {
    var group = element.getAttribute('data-selectable');
    document.querySelectorAll('[data-selectable="' + group + '"]').forEach(function (item) {
      item.classList.remove('active');
    });
    element.classList.add('active');
  });
});
"""


def _header(active: str = "") -> str:
    navigation = (
        ("Услуги", "services"),
        ("Цены", "prices"),
        ("Акции", "offers"),
        ("О сервисе", "about"),
        ("Портфолио", "portfolio"),
        ("Контакты", "contacts"),
    )
    links = "".join(
        f'<a class="{"active" if key == active else ""}" href="#">{label}</a>'
        for label, key in navigation
    )
    return (
        '<header class="th-header">'
        '<div class="th-logo" aria-label="ТОЧКА ХОДА">ТОЧКА<strong>Х</strong>ОДА'
        '<small>АВТОСЕРВИС</small></div>'
        f'<nav class="th-nav">{links}</nav>'
        '<div class="th-phone"><strong>+7 (495) 128-95-95</strong>'
        '<span>Ежедневно с 9:00 до 21:00</span></div>'
        '<button class="th-primary">Записаться</button>'
        '</header>'
    )


def _image(source: str, alt: str, class_name: str = "") -> str:
    class_attr = f' class="{class_name}"' if class_name else ""
    return (
        f'<img{class_attr} src="{escape_html(source)}" '
        f'alt="{escape_html(alt)}" />'
    )


def _asset(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
    key: str,
) -> str:
    try:
        return assets[key]
    except KeyError as exc:
        raise KeyError(
            f"tochka-hoda renderer route {shot.key} is missing asset {key}"
        ) from exc


def _root(shot: ShotSpec, content: str) -> str:
    return (
        f'<main class="th-page th-{shot.key}" data-site="tochka-hoda" '
        f'data-route="{escape_html(shot.key)}">{content}</main>'
    )


def _trust_item(icon_name: str, title: str, copy: str) -> str:
    return (
        '<div class="th-trust-item">'
        f'<span class="th-icon">{icon(icon_name)}</span>'
        f'<div><strong>{title}</strong><span>{copy}</span></div>'
        '</div>'
    )


def _cover(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    photo = _asset(project, shot, assets, "workshop_hero")
    services = (
        ("Техническое обслуживание", "Регламентное ТО с сохранением гарантии"),
        ("Диагностика", "Комплексная проверка всех систем автомобиля"),
        ("Ремонт двигателя", "От замены ГРМ до капитального ремонта"),
        ("Ремонт ходовой", "Диагностика и ремонт подвески любой сложности"),
        ("Электрика", "Поиск и устранение неисправностей"),
        ("Шиномонтаж", "Профессиональный уход за колёсами"),
    )
    service_html = "".join(
        f'<article class="th-service-item"><h3>{title}</h3><p>{copy}</p></article>'
        for title, copy in services
    )
    trust = "".join(
        (
            _trust_item("shield-check", "Гарантия", "до 24 месяцев"),
            _trust_item("settings", "Опыт работы", "более 10 лет"),
            _trust_item("users", "Специалисты", "высокой квалификации"),
            _trust_item("thumbs-up", "Более 12 000", "довольных клиентов"),
        )
    )
    return _root(
        shot,
        _header()
        + '<section class="th-home-hero">'
        '<div class="th-home-copy">'
        '<h1>Техническое обслуживание вашего автомобиля</h1>'
        '<p>Профессионально. Честно. В срок.</p>'
        '<div class="th-offer"><div class="th-offer-mark">'
        f'{icon("activity", size=46)}</div><div><h2>Комплексная диагностика<br />по 41 параметру</h2>'
        '<div class="th-offer-actions"><span class="th-offer-price">990 ₽</span>'
        '<button class="th-primary">Записаться на диагностику</button></div></div>'
        '<div class="th-offer-note">Проверим ходовую, двигатель, электронику и системы безопасности</div>'
        '</div></div>'
        f'<figure class="th-home-photo">{_image(photo, "Автомобиль на посту развал-схождения")}</figure>'
        f'<div class="th-trust-row">{trust}</div></section>'
        '<section class="th-home-services"><div class="th-home-services-head">'
        '<span>Наши услуги</span><h2>Что мы делаем</h2></div>'
        f'<div class="th-service-grid">{service_html}</div>'
        '<div class="th-services-link"><button class="th-secondary">Смотреть все услуги</button></div>'
        '</section>',
    )


def _diagnostics(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> str:
    photo = _asset(project, shot, assets, "diagnostic_closeup")
    packages = (
        ("Базовая", "Оценка состояния основных систем", "activity"),
        ("Комплексная", "Расширенная проверка всех систем", "car-front"),
        ("Перед покупкой", "Полная проверка перед покупкой", "shield-check"),
    )
    package_html = "".join(
        '<div class="th-package{}" data-selectable="package">'
        '<span class="th-icon">{}</span><div><strong>{}</strong><span>{}</span></div></div>'.format(
            " active" if index == 0 else "",
            icon(icon_name),
            title,
            copy,
        )
        for index, (title, copy, icon_name) in enumerate(packages)
    )
    check_groups = (
        ("Двигатель и управление", ("Считывание кодов неисправностей", "Система управления двигателем", "Катушки зажигания и свечи", "Компрессия в цилиндрах", "Топливная система", "Система охлаждения", "Система впуска воздуха", "Турбонаддув / наддув", "Система вентиляции картера")),
        ("Трансмиссия", ("Состояние АКПП / МКПП", "Уровень и состояние масла", "Работа сцепления", "Переключение передач", "Приводные валы", "Раздаточная коробка")),
        ("Тормозная система", ("Износ тормозных колодок", "Состояние дисков", "Уровень тормозной жидкости", "Работа ABS, DSC, ESP", "Стояночный тормоз")),
        ("Ходовая часть", ("Состояние амортизаторов", "Рычаги и сайлентблоки", "Шаровые опоры", "Ступичные подшипники", "Рулевые тяги", "Пыльники и люфты")),
    )
    groups_html = "".join(
        f'<article class="th-check-group"><h3><span class="th-icon">{icon("check")}</span>'
        f'<span>{title}</span><span class="th-check-count">{len(items)}</span></h3>'
        f'<ol>{"".join(f"<li>{item}</li>" for item in items)}</ol></article>'
        for title, items in check_groups
    )
    included_checks = (
        "Чтение и расшифровка ошибок",
        "Проверка двигателя и трансмиссии",
        "Проверка ходовой части",
        "Проверка тормозной системы",
        "Проверка систем безопасности",
    )
    included_html = "".join(
        f'<div class="th-check-line">{icon("check", size=16)}'
        f'<span>{item}</span></div>'
        for item in included_checks
    )
    proof = "".join(
        (
            _trust_item("shield-check", "Гарантия на работы", "до 24 месяцев"),
            _trust_item("settings", "Опыт работы", "более 10 лет"),
            _trust_item("users", "Специалисты", "высокой квалификации"),
            _trust_item("thumbs-up", "Более 12 000", "довольных клиентов"),
            _trust_item("activity", "Оригинальное", "оборудование и ПО"),
            _trust_item("lock", "Конфиденциальность", "ваших данных"),
        )
    )
    return _root(
        shot,
        _header("services")
        + '<section class="th-diagnostic-top"><div class="th-diagnostic-copy">'
        '<div class="th-breadcrumbs">Главная <span>›</span> Услуги <span>›</span> Диагностика</div>'
        '<h1>Диагностика автомобиля</h1><div class="th-diagnostic-price">41 параметр проверки <strong>от 990 ₽</strong></div>'
        '<div class="th-package-panel"><div class="th-package-list">'
        f'{package_html}</div><div class="th-package-detail"><div class="th-check-list">'
        f'{included_html}'
        '</div><div class="th-package-total"><span>Время выполнения<br /><b>от 45 минут</b></span>'
        '<span>Стоимость<br /><strong>от 990 ₽</strong></span></div></div></div>'
        '<div class="th-diagnostic-action"><button class="th-primary">Записаться</button>'
        '<span>Гарантия на работы и сохранность данных</span></div></div>'
        f'<figure class="th-diagnostic-photo">{_image(photo, "Мастер выполняет компьютерную диагностику")}</figure></section>'
        f'<section class="th-proof-strip">{proof}</section>'
        '<section class="th-diagnostic-checklist"><h2>Что входит в диагностику</h2>'
        '<p>41 пункт проверки по единому регламенту сервиса</p>'
        f'<div class="th-check-columns">{groups_html}</div></section>',
    )


def _calendar_days() -> str:
    values = (
        ("Пн", ""), ("Вт", ""), ("Ср", ""), ("Чт", ""), ("Пт", ""), ("Сб", ""), ("Вс", ""),
        ("27", "muted"), ("28", "muted"), ("29", "muted"), ("30", "muted"), ("31", "muted"), ("1", ""), ("2", ""),
        ("3", ""), ("4", ""), ("5", ""), ("6", ""), ("7", ""), ("8", ""), ("9", ""),
        ("10", ""), ("11", ""), ("12", ""), ("13", ""), ("14", ""), ("15", ""), ("16", ""),
        ("17", ""), ("18", ""), ("19", ""), ("20", ""), ("21", ""), ("22", ""), ("23", ""),
        ("24", ""), ("25", ""), ("26", "selected"), ("27", ""), ("28", ""), ("29", ""), ("30", ""),
    )
    return "".join(f'<span class="{class_name}">{value}</span>' for value, class_name in values)


def _booking(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    photo = _asset(project, shot, assets, "service_lounge")
    flow = (
        ("Запись", "Вы выбираете дату и время онлайн"),
        ("Встреча", "Принимаем автомобиль без ожидания"),
        ("Диагностика", "Проверяем по 41 параметру"),
        ("Результаты", "Объясняем выводы и рекомендации"),
        ("Забота об авто", "Выполняем только согласованные работы"),
    )
    flow_html = "".join(
        f'<div class="th-flow-item"><b>{index}</b><span class="th-icon">{icon(icon_name)}</span>'
        f'<strong>{title}</strong><span>{copy}</span></div>'
        for index, ((title, copy), icon_name) in enumerate(
            zip(flow, ("calendar", "car-front", "activity", "check", "shield-check")),
            start=1,
        )
    )
    return _root(
        shot,
        _header()
        + '<section class="th-booking-title"><div class="th-breadcrumbs">Главная <span>›</span> Запись на диагностику</div>'
        '<h1>Запись на диагностику</h1><p>Заполните шаги ниже — мы подготовим всё для вашего визита</p></section>'
        '<section class="th-booking-grid"><div class="th-steps">'
        '<div class="th-step"><div class="th-step-label"><b class="th-step-number">1</b><div><strong>Автомобиль</strong><span>Выберите автомобиль</span></div></div>'
        '<div class="th-step-content"><div class="th-selected-row"><div class="th-selected-main">'
        f'<span class="th-icon">{icon("car-front")}</span><div><strong>BMW X5</strong><span>А123ВС777 · автомобиль подтверждён</span></div></div>'
        '<button class="th-change">Изменить</button></div></div></div>'
        '<div class="th-step"><div class="th-step-label"><b class="th-step-number">2</b><div><strong>Услуга</strong><span>Выберите пакет диагностики</span></div></div>'
        '<div class="th-step-content"><div class="th-selected-row"><div class="th-selected-main">'
        f'<span class="th-icon">{icon("activity")}</span><div><strong>Комплексная диагностика</strong><span>Проверка по 41 параметру всех систем</span></div></div>'
        '<div><strong>1 990 ₽</strong><button class="th-change">Изменить</button></div></div></div></div>'
        '<div class="th-step"><div class="th-step-label"><b class="th-step-number">3</b><div><strong>Дата и время</strong><span>Выберите удобные дату и время</span></div></div>'
        '<div class="th-step-content"><div class="th-date-layout"><div class="th-calendar">'
        '<div class="th-calendar-head"><span>‹</span><span>Август 2026</span><span>›</span></div>'
        f'<div class="th-calendar-grid">{_calendar_days()}</div></div><div class="th-time-panel">'
        '<strong>Доступное время на 26 августа</strong><div class="th-time-list">'
        '<button class="th-time active" data-selectable="time">11:30</button>'
        '<button class="th-time" data-selectable="time">13:00</button>'
        '<button class="th-time" data-selectable="time">16:30</button></div></div></div></div></div>'
        '<div class="th-step"><div class="th-step-label"><b class="th-step-number">4</b><div><strong>Контакты</strong><span>Укажите контактные данные</span></div></div>'
        '<div class="th-step-content"><div class="th-contact-fields">'
        '<div class="th-field"><label>Ваше имя</label><div>Иван Иванов</div></div>'
        '<div class="th-field"><label>Телефон</label><div>+7 (999) 123-45-67</div></div>'
        '<div class="th-field"><label>E-mail</label><div>ivan.ivanov@mail.ru</div></div></div>'
        '<div class="th-consent">☑ Я согласен на обработку персональных данных и получение уведомлений</div></div></div>'
        '</div><aside class="th-order-summary">'
        f'{_image(photo, "Приёмка клиента в сервисе")}<h2>Ваш заказ</h2><div class="th-summary-list">'
        '<div class="th-summary-row"><span>Автомобиль</span><strong>BMW X5 · А123ВС777</strong></div>'
        '<div class="th-summary-row"><span>Услуга</span><strong>Комплексная диагностика</strong></div>'
        '<div class="th-summary-row"><span>Дата и время</span><strong>26 августа 2026 · 11:30</strong></div>'
        '<div class="th-summary-row"><span>Длительность</span><strong>60 минут</strong></div>'
        '<div class="th-summary-row"><span>Адрес</span><strong>Москва, ул. Дорожная, 8</strong></div></div>'
        '<div class="th-summary-total"><span>Итого</span><strong>1 990 ₽</strong></div>'
        '<button class="th-primary">Подтвердить запись</button></aside></section>'
        '<section class="th-booking-bottom"><div class="th-visit-flow"><h2>Как проходит визит</h2>'
        f'<div class="th-flow-items">{flow_html}</div></div>'
        '<div class="th-note-column"><h3>Что взять с собой</h3><ul><li>Водительское удостоверение</li><li>СТС на автомобиль</li><li>Историю предыдущих ремонтов</li><li>Ключи от автомобиля</li></ul></div>'
        '<div class="th-note-column"><h3>Важно знать</h3><ul><li>Отмена записи за 2 часа</li><li>Опоздание более чем на 15 минут</li><li>Сообщим о любых изменениях</li></ul></div></section>',
    )


def _case_study(
    project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]
) -> str:
    before = _asset(project, shot, assets, "bmw_before")
    after = _asset(project, shot, assets, "bmw_after")
    metrics = (
        ("car-front", "Модель", "BMW X5 F15"),
        ("calendar", "Год выпуска", "2018"),
        ("activity", "Пробег", "89 420 км"),
        ("clock", "Время в работе", "1 день"),
        ("wrench", "Итоговая стоимость", "78 650 ₽"),
    )
    metrics_html = "".join(
        f'<div class="th-case-metric"><span class="th-icon">{icon(icon_name)}</span><span>{label}</span><strong>{value}</strong></div>'
        for icon_name, label, value in metrics
    )
    return _root(
        shot,
        _header("portfolio")
        + '<section class="th-case-hero"><div class="th-case-copy">'
        '<div class="th-breadcrumbs">Главная <span>›</span> Портфолио <span>›</span> BMW X5</div>'
        '<h1>BMW X5: устранили стук в ходовой</h1>'
        '<p>Комплексная диагностика и ремонт подвески. Убрали стук спереди и вибрацию руля.</p>'
        f'<div class="th-case-metrics">{metrics_html}</div></div>'
        f'<figure class="th-case-hero-photo">{_image(before, "BMW X5 до ремонта ходовой")}</figure></section>'
        '<section class="th-diagnosis-strip"><div class="th-alert">!</div>'
        '<div class="th-diagnosis-item"><strong>Причина обращения</strong><span>Стук на неровностях и вибрация руля при торможении.</span></div>'
        '<div class="th-diagnosis-item"><strong>Диагностика</strong><span>Проверили подвеску, тормозную систему и углы установки колёс.</span></div>'
        '<div class="th-diagnosis-item"><strong>Вердикт</strong><span>Износ сайлентблоков и коробление передних тормозных дисков.</span></div></section>'
        '<section class="th-case-grid"><article class="th-case-panel"><h2>Что обнаружили</h2>'
        f'<div class="th-finding">{_image(after, "Новые детали подвески и тормозов")}<div class="th-finding-copy">'
        '<section><h3>Износ сайлентблоков передних рычагов</h3><p>Детали потеряли эластичность, что вызывало стук и люфт.</p></section>'
        '<section><h3>Коробление тормозных дисков</h3><p>Биение 0,12 мм передавалось на руль при торможении.</p></section></div>'
        '<div class="th-repair-proof"><div><strong>0 люфтов</strong><span>после ремонта</span></div>'
        '<div><strong>0,03 мм</strong><span>биение дисков</span></div><div><strong>Контрольный замер</strong><span>на стенде 3D</span></div></div></div></article>'
        '<article class="th-case-panel"><h2>Что сделали</h2><ul class="th-work-list">'
        '<li>Заменили сайлентблоки передних нижних рычагов</li><li>Установили новые тормозные диски и колодки</li>'
        '<li>Очистили и смазали направляющие суппортов</li><li>Проверили резьбовые соединения подвески</li><li>Выполнили развал-схождение 3D</li></ul>'
        '<div class="th-parts"><div class="th-part"><span>Сайлентблоки Lemförder, 2 шт.</span><strong>6 400 ₽</strong></div>'
        '<div class="th-part"><span>Тормозные диски Zimmermann, 2 шт.</span><strong>16 800 ₽</strong></div>'
        '<div class="th-part"><span>Тормозные колодки Textar</span><strong>6 200 ₽</strong></div>'
        '<div class="th-part"><span>Работы и материалы</span><strong>49 250 ₽</strong></div></div>'
        '<div class="th-case-total"><span>Стоимость работ и запчастей</span><strong>78 650 ₽</strong></div></article>'
        '<article class="th-case-panel"><h2>Результат</h2><table class="th-result-table"><thead><tr><th>Параметр</th><th>До</th><th>После</th><th>Норма</th></tr></thead>'
        '<tbody><tr><td>Развал передний левый</td><td class="th-before">−0°52′</td><td class="th-after">−0°35′</td><td>−0°30′ ±0°30′</td></tr>'
        '<tr><td>Развал передний правый</td><td class="th-before">−1°05′</td><td class="th-after">−0°34′</td><td>−0°30′ ±0°30′</td></tr>'
        '<tr><td>Схождение суммарное</td><td class="th-before">0°32′</td><td class="th-after">0°10′</td><td>0°10′ ±0°20′</td></tr></tbody></table>'
        '<div class="th-quote">«Стук ушёл сразу после ремонта, руль больше не вибрирует. Машина снова идёт ровно и уверенно».</div>'
        f'<div class="th-warranty">{icon("shield-check")}<strong>Гарантия 24 месяца или 20 000 км на работы и запчасти</strong></div></article></section>',
    )


def _prices(project: ProjectSpec, shot: ShotSpec, assets: Mapping[str, str]) -> str:
    portrait = _asset(project, shot, assets, "mechanic_portrait")
    engine = _asset(project, shot, assets, "engine_inspection")
    categories = (
        ("activity", "Диагностика"),
        ("settings", "Техническое обслуживание"),
        ("wrench", "Двигатель"),
        ("car-front", "Ходовая"),
        ("activity", "Тормозная система"),
        ("settings", "Электрика"),
        ("car-front", "Шиномонтаж"),
    )
    category_html = "".join(
        f'<div class="th-category{" active" if index == 0 else ""}" data-selectable="category">'
        f'<span class="th-icon">{icon(icon_name)}</span><span>{label}</span></div>'
        for index, (icon_name, label) in enumerate(categories)
    )
    rows = (
        ("Компьютерная диагностика", "Считывание кодов ошибок и проверка систем", "от 30 мин", "990 ₽"),
        ("Комплексная диагностика", "Проверка 41 параметра всех систем", "от 60 мин", "1 990 ₽"),
        ("Диагностика перед покупкой", "Полная проверка автомобиля перед покупкой", "от 120 мин", "4 900 ₽"),
        ("Диагностика двигателя", "Проверка питания и навесного оборудования", "от 60 мин", "1 590 ₽"),
        ("Диагностика подвески", "Проверка ходовой части на подъёмнике", "от 45 мин", "1 390 ₽"),
        ("Диагностика тормозной системы", "Проверка механизмов и приводов", "от 30 мин", "990 ₽"),
        ("Диагностика электрики", "Проверка оборудования и проводки", "от 60 мин", "1 590 ₽"),
        ("Проверка кондиционера", "Диагностика давления, утечек и работы системы", "от 45 мин", "1 290 ₽"),
    )
    rows_html = "".join(
        '<tr><td><strong>{}</strong><span>{}</span></td><td>{}</td>'
        '<td><span class="th-price-value">от {}</span></td><td><button class="th-row-action">Записаться</button></td></tr>'.format(
            title, copy, duration, price
        )
        for title, copy, duration, price in rows
    )
    return _root(
        shot,
        _header("prices")
        + '<section class="th-prices-title"><div class="th-breadcrumbs">Главная <span>›</span> Цены</div>'
        '<h1>Цены на услуги</h1><p>Прозрачные цены. Без скрытых доплат. Гарантия на работы и запчасти.</p></section>'
        '<section class="th-prices-main"><aside class="th-category-list">'
        f'{category_html}</aside><div class="th-table-panel"><h2>Диагностика</h2><div class="th-price-filters">'
        f'<button class="th-filter">Все марки {icon("chevron-down", size=14)}</button>'
        f'<button class="th-filter">Все модели {icon("chevron-down", size=14)}</button>'
        f'<button class="th-filter">Все типы {icon("chevron-down", size=14)}</button></div>'
        '<table class="th-price-table"><thead><tr><th>Услуга</th><th>Время</th><th>Стоимость работ</th><th></th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div><aside class="th-consultant"><h2>Ваш сервисный консультант</h2>'
        f'{_image(portrait, "Сервисный консультант Алексей Соколов")}<h3>Алексей Соколов</h3><p>Сервисный консультант</p>'
        '<div class="th-contact-list">'
        f'<div class="th-contact-line">{icon("phone", size=16)}<span>+7 (495) 128-95-95</span></div>'
        f'<div class="th-contact-line">{icon("message-circle", size=16)}<span>Написать в WhatsApp</span></div>'
        f'<div class="th-contact-line">{icon("clock", size=16)}<span>Ежедневно с 9:00 до 21:00</span></div></div>'
        '<button class="th-secondary">Перезвоните мне</button></aside></section>'
        '<section class="th-prices-bottom"><article class="th-bottom-panel"><h2>Цена фиксируется до начала работ</h2>'
        '<p>После согласования перечня работ стоимость закрепляется в заказ-наряде.</p>'
        '<ul class="th-policy-points"><li>Фиксируем стоимость</li><li>Согласовываем детали</li><li>Без доплат без согласия</li></ul>'
        f'{_image(engine, "Проверка двигателя перед согласованием работ", "th-policy-photo")}</article>'
        '<article class="th-bottom-panel"><h2>Актуальные предложения</h2><div class="th-offers">'
        '<div class="th-offer-line"><strong>Бесплатная диагностика</strong><strong>0 ₽</strong></div>'
        '<div class="th-offer-line"><strong>Скидка 10% на работы</strong><strong>−10%</strong></div>'
        '<div class="th-offer-line"><strong>Сезонное хранение шин</strong><strong>0 ₽</strong></div></div></article>'
        '<article class="th-bottom-panel"><h2>Запчасти и материалы</h2><ul class="th-parts-list"><li>Проверенные поставщики</li>'
        '<li>Оригинальные запчасти и аналоги</li><li>Расходные материалы в наличии</li><li>Подбор по VIN</li></ul></article>'
        '<article class="th-bottom-panel"><h2>Гарантия на работы и запчасти</h2><div class="th-warranty-big">'
        f'{icon("shield-check")}<div><strong>До 24 месяцев на работы</strong><span>До 12 месяцев на установленные запчасти</span></div></div></article></section>',
    )


_RENDERERS: dict[
    str,
    Callable[[ProjectSpec, ShotSpec, Mapping[str, str]], str],
] = {
    "cover": _cover,
    "diagnostics": _diagnostics,
    "booking": _booking,
    "case-study": _case_study,
    "prices": _prices,
}


def render(
    project: ProjectSpec,
    shot: ShotSpec,
    assets: Mapping[str, str],
) -> RenderedPage:
    """Render one Tochka Hoda route from its project-owned asset inventory."""
    if project.slug != "tochka-hoda":
        raise KeyError(
            f"tochka-hoda renderer cannot render project {project.slug}"
        )
    try:
        renderer = _RENDERERS[shot.key]
    except KeyError as exc:
        raise ValueError(
            f"tochka-hoda renderer does not support route {shot.key}"
        ) from exc
    html = renderer(project, shot, assets)
    return RenderedPage(html=html, css=_CSS, scripts=_SCRIPTS)
