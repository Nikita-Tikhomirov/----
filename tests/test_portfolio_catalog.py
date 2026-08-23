from portfolio.kwork_pack.catalog import PROJECTS, get_project, public_url


def test_catalog_contains_fifteen_distinct_projects_and_sixty_shots():
    assert len(PROJECTS) == 15
    assert len({project.slug for project in PROJECTS}) == 15
    assert sum(len(project.shots) for project in PROJECTS) == 60
    assert [shot.key for project in PROJECTS for shot in project.shots] == [
        "cover", "content", "function", "mobile"
    ] * 15


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


def test_tochka_hoda_uses_automotive_content_path():
    project = get_project("tochka-hoda")
    assert project.domain == "tochka-hoda.ru"
    assert project.shots[1].public_path == "/uslugi/diagnostika-avtomobilya"
