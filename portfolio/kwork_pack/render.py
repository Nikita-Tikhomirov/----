import base64
import mimetypes
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import url2pathname

from playwright.sync_api import BrowserContext, sync_playwright

from .models import ProjectSpec, ShotSpec
from .shell import build_document
from .sites import render_site


AssetResolver = Callable[[Path, ProjectSpec], Mapping[str, str]]
_VIEWPORT = {"width": 1920, "height": 1280}
_IMAGE_TIMEOUT_MS = 15_000


@dataclass(frozen=True)
class _RenderRequest:
    project: ProjectSpec
    shot: ShotSpec
    destination: Path
    assets: Mapping[str, str]


def output_path(output_root: Path, project: ProjectSpec, shot: ShotSpec) -> Path:
    """Return the stable numbered PNG path for a declared project shot."""
    try:
        shot_number = project.shots.index(shot) + 1
    except ValueError as exc:
        raise ValueError(
            f"Project {project.slug} does not declare shot {shot.key}"
        ) from exc
    return Path(output_root) / project.slug / f"{shot_number:02d}-{shot.key}.png"


def _file_uri_to_path(uri: str) -> Path:
    parsed = urlsplit(uri)
    pathname = urlunsplit(("", parsed.netloc, parsed.path, "", ""))
    return Path(url2pathname(pathname))


def _stage_local_assets(
    project: ProjectSpec, assets: Mapping[str, str]
) -> dict[str, str]:
    staged_assets = {}
    for key, uri in assets.items():
        parsed = urlsplit(uri)
        if parsed.scheme != "file":
            raise ValueError(
                f"Asset {project.slug}/{key} must be a local file URI, got {uri!r}"
            )
        asset_path = _file_uri_to_path(uri)
        if not asset_path.is_file():
            raise FileNotFoundError(
                f"Asset {project.slug}/{key} does not exist: {asset_path}"
            )
        media_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
        staged_assets[key] = f"data:{media_type};base64,{encoded}"
    return staged_assets


def _default_asset_resolver(
    output_root: Path, project: ProjectSpec
) -> Mapping[str, str]:
    try:
        from .assets import resolve_project_assets
    except ModuleNotFoundError as exc:
        if exc.name != "portfolio.kwork_pack.assets":
            raise
        raise RuntimeError(
            "The portfolio asset resolver is unavailable; pass asset_resolver "
            f"for project {project.slug} under {output_root}"
        ) from exc
    return resolve_project_assets(output_root, project)


def _prepare_project(
    project: ProjectSpec,
    shots: Iterable[ShotSpec],
    output_root: Path,
    asset_resolver: AssetResolver,
) -> tuple[_RenderRequest, ...]:
    selected_shots = tuple(shots)
    destinations = tuple(
        output_path(output_root, project, shot) for shot in selected_shots
    )
    assets = _stage_local_assets(
        project, asset_resolver(output_root, project)
    )
    return tuple(
        _RenderRequest(project, shot, destination, assets)
        for shot, destination in zip(selected_shots, destinations)
    )


def _render_page(
    context: BrowserContext,
    project: ProjectSpec,
    shot: ShotSpec,
    destination: Path,
    assets: Mapping[str, str],
) -> None:
    page = context.new_page()
    try:
        page_html = render_site(project, shot, dict(assets))
        document = build_document(project, shot, page_html, "")
        page.set_content(document, wait_until="load")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_function(
            "() => Array.from(document.images).every("
            "image => image.complete && image.naturalWidth > 0)",
            timeout=_IMAGE_TIMEOUT_MS,
        )
        page.screenshot(
            path=destination,
            full_page=False,
            animations="disabled",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to render {project.slug}/{shot.key} to {destination}: {exc}"
        ) from exc
    finally:
        page.close()


def _render_requests(
    requests: tuple[_RenderRequest, ...], chrome_channel: str
) -> tuple[Path, ...]:
    if not requests:
        return ()
    for request in requests:
        request.destination.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=chrome_channel, headless=True)
        try:
            context = browser.new_context(
                viewport=_VIEWPORT,
                device_scale_factor=1,
                reduced_motion="reduce",
                color_scheme="light",
                locale="ru-RU",
                timezone_id="Europe/Moscow",
            )
            try:
                for request in requests:
                    _render_page(
                        context,
                        request.project,
                        request.shot,
                        request.destination,
                        request.assets,
                    )
            finally:
                context.close()
        finally:
            browser.close()
    return tuple(request.destination for request in requests)


def render_shot(
    project: ProjectSpec,
    shot: ShotSpec,
    output_root: Path,
    *,
    chrome_channel: str = "chrome",
    asset_resolver: AssetResolver | None = None,
) -> Path:
    """Render one declared shot to an exact 1920x1280 PNG."""
    root = Path(output_root)
    resolver = asset_resolver or _default_asset_resolver
    requests = _prepare_project(project, (shot,), root, resolver)
    return _render_requests(requests, chrome_channel)[0]


def render_project(
    project: ProjectSpec,
    output_root: Path,
    *,
    chrome_channel: str = "chrome",
    asset_resolver: AssetResolver | None = None,
) -> tuple[Path, ...]:
    """Render all four declared project shots in one isolated browser context."""
    root = Path(output_root)
    resolver = asset_resolver or _default_asset_resolver
    requests = _prepare_project(project, project.shots, root, resolver)
    return _render_requests(requests, chrome_channel)


def render_all(
    projects: Iterable[ProjectSpec],
    output_root: Path,
    *,
    chrome_channel: str = "chrome",
    asset_resolver: AssetResolver | None = None,
) -> tuple[Path, ...]:
    """Render projects in catalog order using one Chrome browser and context."""
    root = Path(output_root)
    resolver = asset_resolver or _default_asset_resolver
    requests = tuple(
        request
        for project in projects
        for request in _prepare_project(project, project.shots, root, resolver)
    )
    return _render_requests(requests, chrome_channel)
