from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

import portfolio.kwork_pack.render as renderer
from portfolio.kwork_pack.catalog import get_project
from portfolio.kwork_pack.render import output_path, render_all, render_project, render_shot


class RecordingPage:
    def __init__(self, context):
        self.context = context
        self.html = ""
        self.wait_until = None
        self.closed = False

    def set_content(self, html, *, wait_until):
        self.html = html
        self.wait_until = wait_until

    def evaluate(self, expression):
        self.context.evaluations.append(expression)

    def wait_for_function(self, expression, *, timeout):
        self.context.image_waits.append((expression, timeout))

    def screenshot(self, *, path, full_page, animations):
        self.context.screenshots.append((Path(path), full_page, animations))
        Image.new("RGB", (1920, 1280), "#d7dde2").save(path)

    def close(self):
        self.closed = True


class RecordingContext:
    def __init__(self):
        self.pages = []
        self.evaluations = []
        self.image_waits = []
        self.screenshots = []
        self.closed = False

    def new_page(self):
        page = RecordingPage(self)
        self.pages.append(page)
        return page

    def close(self):
        self.closed = True


class RecordingBrowser:
    def __init__(self):
        self.context = RecordingContext()
        self.context_options = None
        self.closed = False

    def new_context(self, **options):
        self.context_options = options
        return self.context

    def close(self):
        self.closed = True


class RecordingChromium:
    def __init__(self):
        self.browser = RecordingBrowser()
        self.launch_options = None

    def launch(self, **options):
        self.launch_options = options
        return self.browser


class RecordingPlaywright:
    def __init__(self):
        self.chromium = RecordingChromium()
        self.exited = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.exited = True


@pytest.fixture
def recording_playwright(monkeypatch):
    recording = RecordingPlaywright()
    monkeypatch.setattr(renderer, "sync_playwright", lambda: recording)
    return recording


@pytest.fixture
def local_asset(tmp_path):
    path = tmp_path / "assets" / "tochka-hoda" / "hero.png"
    path.parent.mkdir(parents=True)
    Image.new("RGB", (1600, 900), "#d7dde2").save(path)
    return path


def asset_resolver_for(path):
    def resolve(_output_root, _project):
        return {"hero": path.resolve().as_uri()}

    return resolve


def test_output_path_uses_stable_numbered_names(tmp_path):
    project = get_project("tochka-hoda")

    assert output_path(tmp_path, project, project.shots[0]) == (
        tmp_path / "tochka-hoda" / "01-cover.png"
    )
    assert output_path(tmp_path, project, project.shots[3]).name == "04-mobile.png"


def test_output_path_rejects_a_shot_outside_the_project(tmp_path):
    project = get_project("tochka-hoda")
    unknown_shot = replace(project.shots[0], key="unknown")

    with pytest.raises(ValueError, match="tochka-hoda.*unknown"):
        output_path(tmp_path, project, unknown_shot)


def test_render_project_writes_four_shots_with_semantic_urls_and_fixed_context(
    tmp_path, local_asset, recording_playwright
):
    project = get_project("tochka-hoda")

    paths = render_project(
        project,
        tmp_path,
        asset_resolver=asset_resolver_for(local_asset),
    )

    assert paths == tuple(output_path(tmp_path, project, shot) for shot in project.shots)
    assert all(path.is_file() for path in paths)

    chromium = recording_playwright.chromium
    browser = chromium.browser
    context = browser.context
    assert chromium.launch_options == {"channel": "chrome", "headless": True}
    assert context.pages[0].wait_until == "load"
    assert "https://tochka-hoda.ru/" in context.pages[0].html
    assert "https://tochka-hoda.ru/uslugi/diagnostika-avtomobilya" in context.pages[3].html
    assert 'class="browser-url-bar"' in context.pages[0].html
    assert 'class="mobile-url-bar"' in context.pages[3].html
    assert browser.context_options["viewport"] == {"width": 1920, "height": 1280}
    assert browser.context_options["device_scale_factor"] == 1
    assert browser.context_options["reduced_motion"] == "reduce"
    assert all(not full_page and animations == "disabled" for _, full_page, animations in context.screenshots)
    assert all(page.closed for page in context.pages)
    assert context.closed is True
    assert browser.closed is True
    assert recording_playwright.exited is True


@pytest.mark.parametrize("slug", ("okna-sfera", "sever-market"))
def test_render_project_dispatches_noncommercial_site_groups(
    slug, tmp_path, local_asset, recording_playwright
):
    project = get_project(slug)

    paths = render_project(
        project,
        tmp_path,
        asset_resolver=asset_resolver_for(local_asset),
    )

    assert len(paths) == 4
    assert f'data-project="{slug}"' in recording_playwright.chromium.browser.context.pages[0].html


def test_render_all_preserves_project_and_shot_order_in_one_browser(
    tmp_path, local_asset, recording_playwright
):
    projects = (get_project("tochka-hoda"), get_project("okna-sfera"))

    paths = render_all(
        projects,
        tmp_path,
        asset_resolver=asset_resolver_for(local_asset),
    )

    assert paths == tuple(
        output_path(tmp_path, project, shot)
        for project in projects
        for shot in project.shots
    )
    assert len(recording_playwright.chromium.browser.context.pages) == 8


def test_missing_local_asset_reports_the_project_key_and_path(tmp_path):
    project = get_project("tochka-hoda")
    missing = tmp_path / "assets" / project.slug / "hero.png"

    with pytest.raises(
        FileNotFoundError,
        match=r"tochka-hoda/hero.*assets.*tochka-hoda.*hero\.png",
    ):
        render_shot(
            project,
            project.shots[0],
            tmp_path,
            asset_resolver=asset_resolver_for(missing),
        )


def test_renderer_rejects_network_assets_before_launch(tmp_path):
    project = get_project("tochka-hoda")

    with pytest.raises(ValueError, match=r"tochka-hoda/hero.*local file URI"):
        render_shot(
            project,
            project.shots[0],
            tmp_path,
            asset_resolver=lambda _root, _project: {
                "hero": "https://example.test/hero.png"
            },
        )


def test_render_error_names_output_and_closes_browser_resources(
    tmp_path, local_asset, recording_playwright
):
    project = get_project("tochka-hoda")
    context = recording_playwright.chromium.browser.context

    def new_failing_page():
        page = RecordingPage(context)

        def fail_image_wait(_expression, *, timeout):
            raise TimeoutError(f"images did not load in {timeout}ms")

        page.wait_for_function = fail_image_wait
        context.pages.append(page)
        return page

    context.new_page = new_failing_page

    with pytest.raises(
        RuntimeError,
        match=r"tochka-hoda/cover.*01-cover\.png.*images did not load",
    ):
        render_shot(
            project,
            project.shots[0],
            tmp_path,
            asset_resolver=asset_resolver_for(local_asset),
        )

    assert context.pages[0].closed is True
    assert context.closed is True
    assert recording_playwright.chromium.browser.closed is True
    assert recording_playwright.exited is True


def test_real_chrome_render_is_exact_size_and_nonblank(tmp_path, local_asset):
    project = get_project("tochka-hoda")

    path = render_shot(
        project,
        project.shots[0],
        tmp_path,
        asset_resolver=asset_resolver_for(local_asset),
    )

    with Image.open(path) as image:
        assert image.size == (1920, 1280)
        assert image.mode in {"RGB", "RGBA"}
        assert any(low < high for low, high in image.convert("RGB").getextrema())
