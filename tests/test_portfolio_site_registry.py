import sys
from dataclasses import dataclass
from types import ModuleType

import pytest

from portfolio.kwork_pack.catalog import PROJECTS, get_project
import portfolio.kwork_pack.sites as sites


@dataclass(frozen=True)
class DedicatedPage:
    html: str
    css: str
    scripts: str = ""


def _registry_api(name):
    candidate = getattr(sites, name, None)
    assert callable(candidate), f"portfolio.kwork_pack.sites.{name} must be callable"
    return candidate


def _semantic_assets(project):
    return {asset.key: f"/{asset.filename}" for asset in project.assets}


def _dedicated_module(project, marker="dedicated"):
    module = ModuleType(project.renderer_module)

    def render(_project, _shot, _assets):
        return DedicatedPage(f'<main data-renderer="{marker}"></main>', ".site {}")

    module.render = render
    return module


def test_each_project_resolves_a_dedicated_renderer_module(monkeypatch):
    for project in PROJECTS:
        monkeypatch.setitem(sys.modules, project.renderer_module, _dedicated_module(project))

    get_renderer_module = _registry_api("get_renderer_module")
    modules = [get_renderer_module(project) for project in PROJECTS]

    assert len(set(module.__name__ for module in modules)) == 15
    assert all(
        module.__name__.rsplit(".", 1)[-1] == project.slug.replace("-", "_")
        for module, project in zip(modules, PROJECTS)
    )


def test_get_renderer_returns_the_declared_callable(monkeypatch):
    project = get_project("tochka-hoda")
    module = _dedicated_module(project)
    monkeypatch.setitem(sys.modules, project.renderer_module, module)

    assert _registry_api("get_renderer")(project) is module.render


def test_get_renderer_module_rejects_a_module_with_the_wrong_final_name(monkeypatch):
    project = get_project("tochka-hoda")
    module = _dedicated_module(project)
    module.__name__ = "portfolio.kwork_pack.sites.other_project"
    monkeypatch.setitem(sys.modules, project.renderer_module, module)

    with pytest.raises(ValueError, match=r"tochka-hoda.*tochka_hoda.*other_project"):
        _registry_api("get_renderer_module")(project)


def test_get_renderer_rejects_a_missing_render_callable(monkeypatch):
    project = get_project("tochka-hoda")
    module = ModuleType(project.renderer_module)
    monkeypatch.setitem(sys.modules, project.renderer_module, module)

    with pytest.raises(TypeError, match=r"tochka-hoda.*tochka_hoda.*render"):
        _registry_api("get_renderer")(project)


def test_render_site_prefers_an_exact_dedicated_module_over_legacy_dispatch(monkeypatch):
    project = get_project("tochka-hoda")
    module = _dedicated_module(project)
    monkeypatch.setitem(sys.modules, project.renderer_module, module)

    page = _registry_api("render_site")(project, project.shots[0], _semantic_assets(project))

    assert page.html == '<main data-renderer="dedicated"></main>'
    assert page.css == ".site {}"


def test_render_site_wraps_legacy_output_only_when_the_declared_module_is_absent():
    project = get_project("tochka-hoda")

    page = _registry_api("render_site")(project, project.shots[0], _semantic_assets(project))

    assert f'data-project="{project.slug}"' in page.html
    assert page.css == ""
    assert page.scripts == ""


def test_render_site_propagates_dependency_import_failures(monkeypatch):
    project = get_project("tochka-hoda")
    missing_dependency = "portfolio.kwork_pack.dependencies.missing"

    def import_with_dependency_failure(module_name):
        assert module_name == project.renderer_module
        raise ModuleNotFoundError("missing dependency", name=missing_dependency)

    monkeypatch.setattr(sites, "import_module", import_with_dependency_failure, raising=False)

    with pytest.raises(ModuleNotFoundError) as error:
        _registry_api("render_site")(project, project.shots[0], _semantic_assets(project))

    assert error.value.name == missing_dependency


def test_render_site_does_not_fallback_when_a_declared_module_has_no_render(monkeypatch):
    project = get_project("tochka-hoda")
    module = ModuleType(project.renderer_module)
    monkeypatch.setitem(sys.modules, project.renderer_module, module)

    with pytest.raises(TypeError, match=r"tochka-hoda.*render"):
        _registry_api("render_site")(project, project.shots[0], _semantic_assets(project))
