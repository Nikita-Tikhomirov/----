from .models import AssetSpec, ProjectSpec, ShotSpec


PROJECT_IDENTITIES = (
    ("tochka-hoda", "tochka-hoda.ru", "Сайт автосервиса «Точка Хода»"),
    ("dentalea", "dentalea-clinic.ru", "Сайт стоматологии «Денталея»"),
    ("ventkontur", "ventkontur.ru", "Каталог вентиляции «ВентКонтур»"),
    ("syr-hleb", "syr-hleb.ru", "Интернет-магазин «Сыр и Хлеб»"),
    ("kvadrat-remonta", "kvadrat-remonta.ru", "Сайт ремонта квартир"),
    ("okna-sfera", "okna-sfera.ru", "Лендинг пластиковых окон"),
    ("chistiy-metr", "chistiy-metr.ru", "Лендинг клининговой компании"),
    ("teplodom", "teplodom-service.ru", "Лендинг ремонта котлов"),
    ("pereezd-prosto", "berezhny-pereezd.ru", "Лендинг квартирных переездов"),
    ("pravo-opora", "pravovaya-opora.ru", "Лендинг юридической компании"),
    ("sever-market", "severniy-marshrut.ru", "Магазин туристического снаряжения"),
    ("modulprof", "modulprof.ru", "B2B-каталог модульных зданий"),
    ("doma-u-ozera", "doma-u-ozera.ru", "Сервис бронирования домов"),
    ("praktika", "praktika-navyka.ru", "Образовательная платформа"),
    ("gruzcontrol", "gruzcontrol.ru", "Кабинет управления доставками"),
)

_PROJECT_DETAILS = {
    "tochka-hoda": ("Точка Хода", "Коммерческие сайты", "/uslugi/diagnostika-avtomobilya", "graphite-green-red"),
    "dentalea": ("Денталея", "Коммерческие сайты", "/uslugi/implantatsiya-zubov", "mint-coral-graphite"),
    "ventkontur": ("ВентКонтур", "Коммерческие сайты", "/catalog/ventilyatsionnye-ustanovki", "steel-yellow-red"),
    "syr-hleb": ("Сыр и Хлеб", "Коммерческие сайты", "/catalog/podarochnye-nabory", "burgundy-herbal"),
    "kvadrat-remonta": ("Квадрат ремонта", "Коммерческие сайты", "/uslugi/remont-kvartir", "blue-brick-graphite"),
    "okna-sfera": ("Окна Сфера", "Лидогенерирующие лендинги", "/plastikovye-okna", "sky-yellow-graphite"),
    "chistiy-metr": ("Чистый метр", "Лидогенерирующие лендинги", "/uborka-posle-remonta", "turquoise-lemon-dark"),
    "teplodom": ("ТеплоДом", "Лидогенерирующие лендинги", "/remont-gazovyh-kotlov", "red-green-gray"),
    "pereezd-prosto": ("Бережный переезд", "Лидогенерирующие лендинги", "/kvartirnyy-pereezd", "cobalt-green-red"),
    "pravo-opora": ("Правовая опора", "Лидогенерирующие лендинги", "/uslugi/spory-s-zastroyshchikom", "forest-gold-burgundy"),
    "sever-market": ("Северный маршрут", "Проекты посложнее", "/catalog/turisticheskoe-snaryazhenie", "pine-red-gray"),
    "modulprof": ("МодульПроф", "Проекты посложнее", "/catalog/modulnye-zdaniya", "graphite-yellow-blue"),
    "doma-u-ozera": ("Дома у озера", "Проекты посложнее", "/booking/dom-s-saunoy", "forest-berry"),
    "praktika": ("Практика", "Проекты посложнее", "/cabinet/courses", "coral-turquoise-black"),
    "gruzcontrol": ("ГрузКонтроль", "Проекты посложнее", "/dashboard/dostavki", "green-red-amber"),
}

_CATEGORY = ("Разработка и IT", "Создание сайта")


def _shots(public_path: str) -> tuple[ShotSpec, ...]:
    return (
        ShotSpec("cover", "/", "desktop", "cover"),
        ShotSpec("content", public_path, "desktop", "content"),
        ShotSpec("function", public_path, "desktop", "function"),
        ShotSpec("mobile", public_path, "mobile", "mobile"),
    )


def _asset(brand: str) -> AssetSpec:
    return AssetSpec(
        key="hero",
        filename="hero.png",
        prompt=f"Предметная фотография для авторского концепта сайта «{brand}», без логотипов и текста",
    )


def _build_project(slug: str, domain: str, title: str) -> ProjectSpec:
    brand, group, public_path, palette = _PROJECT_DETAILS[slug]
    return ProjectSpec(
        slug=slug,
        brand=brand,
        kwork_title=title,
        group=group,
        domain=domain,
        category=_CATEGORY,
        work_type="Новый сайт",
        description=f"Авторский концепт сайта «{brand}»: продуманная структура, интерфейс и сценарий для демонстрации проекта.",
        palette=palette,
        shots=_shots(public_path),
        assets=(_asset(brand),),
    )


PROJECTS: tuple[ProjectSpec, ...] = tuple(
    _build_project(slug, domain, title)
    for slug, domain, title in PROJECT_IDENTITIES
)

_PROJECT_BY_SLUG = {project.slug: project for project in PROJECTS}


def get_project(slug: str) -> ProjectSpec:
    """Return the immutable project record identified by its slug."""
    try:
        return _PROJECT_BY_SLUG[slug]
    except KeyError as exc:
        raise KeyError(f"Unknown portfolio project: {slug}") from exc


def public_url(project: ProjectSpec, shot: ShotSpec) -> str:
    """Build the semantic public URL consumed by browser shells and renderers."""
    path = shot.public_path if shot.public_path.startswith("/") else f"/{shot.public_path}"
    return f"https://{project.domain}{path}"
