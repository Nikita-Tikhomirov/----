import ast
from html import escape
from importlib import import_module
import inspect
import re

import pytest
from playwright.sync_api import sync_playwright

from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.shell import build_document
from portfolio.kwork_pack.sites.runtime import RenderedPage


_ROUTE_COPY = {
    "cover": (
        "Защищаем права в споре, а не продаём обещания",
        "Оценка дела за одну минуту",
        "Четыре шага до результата",
    ),
    "developer-disputes": (
        "Взыскиваем с застройщика по документам и срокам",
        "Матрица требований и сроков",
        "Порядок подачи претензии",
    ),
    "assessment": (
        "Проверьте перспективу дела до консультации",
        "Предварительный правовой путь",
        "Документы к консультации",
    ),
    "practice": (
        "Судебная практика с суммами и сроками",
        "Взыскано по выбранным делам",
        "От претензии до исполнения",
    ),
    "consultation": (
        "Консультация с юристом по вашей категории спора",
        "Подтверждение консультации",
        "Как подготовиться к встрече",
    ),
}

_ASSETS_BY_ROUTE = {
    "cover": ("consultation_table",),
    "developer-disputes": ("office_exterior",),
    "assessment": ("case_documents",),
    "practice": ("courtroom_hall",),
    "consultation": ("lawyer_portrait", "client_meeting"),
}


def _render(project, shot, assets):
    module = import_module("portfolio.kwork_pack.sites.pravo_opora")
    return module.render(project, shot, assets)


def _assets(project):
    return {
        asset.key: f'/assets/{asset.filename}?project=pravo-opora&mode="preview"'
        for asset in project.assets
    }


@pytest.fixture(scope="module")
def chrome_browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        try:
            yield browser
        finally:
            browser.close()


def test_pravo_opora_renders_five_distinct_routes_with_exact_legal_copy():
    project = get_project("pravo-opora")
    pages = [_render(project, shot, _assets(project)) for shot in project.shots]
    assert all(isinstance(page, RenderedPage) for page in pages)
    assert [shot.key for shot in project.shots] == list(_ROUTE_COPY)
    assert len({page.html for page in pages}) == 5
    for shot, page in zip(project.shots, pages):
        assert 'data-site="pravo-opora"' in page.html
        assert f'data-route="{shot.key}"' in page.html
        assert "ПРАВОВАЯ ОПОРА" in page.html
        assert "ЮРИДИЧЕСКОЕ БЮРО" in page.html
        for fragment in _ROUTE_COPY[shot.key]:
            assert fragment in page.html


def test_pravo_opora_uses_each_route_owned_asset_exactly_once():
    project = get_project("pravo-opora")
    assets = _assets(project)
    pages = {
        shot.key: _render(project, shot, assets).html for shot in project.shots
    }
    for route, owned_keys in _ASSETS_BY_ROUTE.items():
        for key in owned_keys:
            source = escape(assets[key], quote=True)
            assert pages[route].count(source) == 1
            assert sum(page.count(source) for page in pages.values()) == 1


def test_pravo_opora_renderer_is_isolated_and_avoids_legal_templates():
    module = import_module("portfolio.kwork_pack.sites.pravo_opora")
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert not any("portfolio.kwork_pack.sites." in name for name in imports)
    assert "linear-gradient" not in source
    assert "radial-gradient" not in source
    assert "backdrop-filter" not in source
    assert "криптовалют" not in source.lower()
    assert "гарантируем победу" not in source.lower()


def test_pravo_opora_css_locks_canvas_and_readable_type():
    project = get_project("pravo-opora")
    page = _render(project, project.shots[0], _assets(project))
    assert "height: 1120px" in page.css
    assert "overflow: hidden" in page.css
    assert "letter-spacing: 0" in page.css
    sizes = [int(value) for value in re.findall(r"font-size:\s*(\d+)px", page.css)]
    assert sizes and min(sizes) >= 12


def test_pravo_opora_real_canvas_has_no_hidden_overflow(chrome_browser):
    project = get_project("pravo-opora")
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        for shot in project.shots:
            rendered = _render(project, shot, _assets(project))
            page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
            canvas = page.locator(".po-page").evaluate(
                "root => ({height: root.getBoundingClientRect().height, scrollHeight: root.scrollHeight})"
            )
            assert canvas == {"height": 1120, "scrollHeight": 1120}
    finally:
        page.close()


def test_pravo_cover_quick_issue_updates_selected_path(chrome_browser):
    project = get_project("pravo-opora")
    shot = next(shot for shot in project.shots if shot.key == "cover")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".po-page").bounding_box()
        option = page.locator('[data-selectable="quick-issue"][data-value="consumer"]')
        assert option.count() == 1
        option.click()
        assert option.get_attribute("aria-pressed") == "true"
        result = page.locator(".po-quick-result").inner_text()
        assert "Претензия продавцу → экспертиза → требование" in result
        assert "договор, чек и срок ответа" in result
        assert page.locator(".po-page").bounding_box() == geometry
    finally:
        page.close()


def test_pravo_developer_claim_updates_matrix_and_recovery(chrome_browser):
    project = get_project("pravo-opora")
    shot = next(shot for shot in project.shots if shot.key == "developer-disputes")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".po-page").bounding_box()
        option = page.locator('[data-selectable="claim"][data-value="defects"]')
        assert option.count() == 1
        option.click()
        assert option.get_attribute("aria-pressed") == "true"
        matrix = page.locator(".po-deadline-matrix").inner_text()
        recovery = page.locator(".po-recovery").inner_text()
        assert "Акт дефектов · квартира передана" in matrix
        assert "Устранение недостатков" in matrix
        assert "780 000 ₽" in recovery
        assert page.locator(".po-page").bounding_box() == geometry
    finally:
        page.close()


def test_pravo_cover_uses_qualified_service_proof_instead_of_bare_statistics():
    project = get_project("pravo-opora")
    shot = next(shot for shot in project.shots if shot.key == "cover")
    page = _render(project, shot, _assets(project))
    assert "82%" not in page.html
    assert "Письменный вывод" in page.html
    assert "Без обещаний результата" in page.html
    assert "Юристы с судебной практикой" in page.html


def test_pravo_assessment_updates_path_deadline_risk_and_documents(chrome_browser):
    project = get_project("pravo-opora")
    shot = next(shot for shot in project.shots if shot.key == "assessment")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".po-page").bounding_box()
        page.locator('[data-selectable="issue"][data-value="delay"]').click()
        page.locator('[data-selectable="contract"][data-value="yes"]').click()
        page.locator('[data-selectable="deadline"][data-value="passed"]').click()
        result = page.locator("[data-assessment-result]").inner_text()
        assert "Неустойка за нарушение срока передачи" in result
        assert "Срок претензии не пропущен" in result
        assert "Риск: средний" in result
        assert "ДДУ и дополнительные соглашения" in result
        assert "Акт приёма-передачи или уведомление" in result
        assert page.locator(".po-page").bounding_box() == geometry
    finally:
        page.close()


def test_pravo_practice_filter_updates_ledger_and_recovered_total(chrome_browser):
    project = get_project("pravo-opora")
    shot = next(shot for shot in project.shots if shot.key == "practice")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".po-page").bounding_box()
        page.locator('[data-selectable="practice-filter"][data-value="developer"]').click()
        ledger = page.locator("[data-practice-ledger]").inner_text()
        assert "4 дела по застройщикам" in ledger
        assert "3 840 000 ₽" in ledger
        assert "Средний срок: 5,5 месяца" in ledger
        assert page.locator(".po-page").bounding_box() == geometry
    finally:
        page.close()


def test_pravo_consultation_updates_lawyer_time_and_case_summary(chrome_browser):
    project = get_project("pravo-opora")
    shot = next(shot for shot in project.shots if shot.key == "consultation")
    rendered = _render(project, shot, _assets(project))
    page = chrome_browser.new_page(viewport={"width": 1920, "height": 1280})
    try:
        page.set_content(build_document(project, shot, rendered.html, rendered.css, rendered.scripts))
        geometry = page.locator(".po-page").bounding_box()
        page.locator('[data-selectable="lawyer"][data-value="orlov"]').click()
        page.locator('[data-selectable="consultation-time"][data-value="18:30"]').click()
        summary = page.locator("[data-consultation-summary]").inner_text()
        assert "Дмитрий Орлов" in summary
        assert "Сегодня · 18:30" in summary
        assert "Споры с застройщиками" in summary
        assert "60 минут · видеосвязь" in summary
        assert page.locator(".po-page").bounding_box() == geometry
    finally:
        page.close()
