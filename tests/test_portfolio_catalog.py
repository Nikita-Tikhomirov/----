from portfolio.kwork_pack.catalog import PROJECTS, get_project, public_url


_LEGACY_DISPATCH_VARIANTS = {"cover", "content", "function"}

_REQUIRED_WORKFLOW_ROUTES = {
    "tochka-hoda": ("booking", "/zapis/diagnostika"),
    "dentalea": ("booking", "/zapis-k-vrachu"),
    "ventkontur": ("selection", "/podbor-oborudovaniya"),
    "syr-hleb": ("builder", "/sobrat-podarochnyy-nabor"),
    "kvadrat-remonta": ("calculator", "/kalkulyator-smety"),
    "okna-sfera": ("calculator", "/raschet-okna"),
    "chistiy-metr": ("calculator", "/raschet-uborki"),
    "teplodom": ("request", "/vyzov-mastera"),
    "pereezd-prosto": ("calculator", "/raschet-pereezda"),
    "pravo-opora": ("assessment", "/otsenka-dela"),
    "sever-market": ("cart", "/korzina"),
    "modulprof": ("configurator", "/konfigurator"),
    "doma-u-ozera": ("booking", "/bronirovanie"),
    "praktika": ("lesson", "/courses/web-design/lesson-4"),
    "gruzcontrol": ("dispatch", "/dashboard/dispatch"),
}


def test_every_project_has_five_desktop_routes_and_dedicated_renderer():
    assert len(PROJECTS) == 15
    assert len({project.slug for project in PROJECTS}) == 15
    assert len({project.renderer_module for project in PROJECTS}) == 15
    for project in PROJECTS:
        assert project.renderer_module == (
            f"portfolio.kwork_pack.sites.{project.slug.replace('-', '_')}"
        )
        assert len(project.shots) == 5
        assert all(shot.layout == "desktop" for shot in project.shots)
        assert len({shot.path for shot in project.shots}) == 5
        assert {shot.variant for shot in project.shots} <= _LEGACY_DISPATCH_VARIANTS
        assert tuple(shot.variant for shot in project.shots) == (
            "cover",
            "content",
            "function",
            "content",
            "function",
        )


def test_catalog_declares_exact_flagship_story_and_all_required_workflows():
    flagship = get_project("tochka-hoda")
    assert [(shot.key, shot.path) for shot in flagship.shots] == [
        ("cover", "/"),
        ("diagnostics", "/uslugi/diagnostika-avtomobilya"),
        ("booking", "/zapis/diagnostika"),
        ("case-study", "/raboty/bmw-x5-hodovaya"),
        ("prices", "/ceny"),
    ]

    for slug, workflow_route in _REQUIRED_WORKFLOW_ROUTES.items():
        project_routes = {(shot.key, shot.path) for shot in get_project(slug).shots}
        assert workflow_route in project_routes


def test_public_urls_are_semantic_and_never_look_like_local_demos():
    for project in PROJECTS:
        assert project.domain.endswith(".ru")
        assert "demo" not in project.domain
        assert "nikita" not in project.domain
        for shot in project.shots:
            url = public_url(project, shot)
            assert url.startswith(f"https://{project.domain}/")
            assert "localhost" not in url


def test_kwork_titles_fit_form_limit_and_identify_author_concepts():
    for project in PROJECTS:
        assert 1 <= len(project.kwork_title) <= 40
        assert "Авторский концепт" in project.description


def test_every_project_declares_a_real_asset_inventory():
    for project in PROJECTS:
        assert len(project.assets) >= 6
        assert len({asset.key for asset in project.assets}) == len(project.assets)
        assert len({asset.filename for asset in project.assets}) == len(project.assets)
        assert all(asset.filename != "hero.png" for asset in project.assets)


def test_tochka_hoda_uses_automotive_content_path():
    project = get_project("tochka-hoda")
    assert project.domain == "tochka-hoda.ru"
    assert project.shots[1].path == "/uslugi/diagnostika-avtomobilya"


def test_moving_and_legal_concepts_use_approved_available_brands_and_domains():
    moving = get_project("pereezd-prosto")
    legal = get_project("pravo-opora")

    assert (moving.brand, moving.domain) == ("Бережный переезд", "berezhny-pereezd.ru")
    assert (legal.brand, legal.domain) == ("Правовая опора", "pravovaya-opora.ru")


def test_store_and_learning_concepts_use_approved_available_brands_and_domains():
    store = get_project("sever-market")
    learning = get_project("praktika")

    assert (store.brand, store.domain) == (
        "Северный маршрут",
        "severniy-marshrut.ru",
    )
    assert learning.domain == "praktika-navyka.ru"
