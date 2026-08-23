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
    "tochka-hoda": ("Точка Хода", "Коммерческие сайты", "graphite-green-red"),
    "dentalea": ("Денталея", "Коммерческие сайты", "mint-coral-graphite"),
    "ventkontur": ("ВентКонтур", "Коммерческие сайты", "steel-yellow-red"),
    "syr-hleb": ("Сыр и Хлеб", "Коммерческие сайты", "burgundy-herbal"),
    "kvadrat-remonta": ("Квадрат ремонта", "Коммерческие сайты", "blue-brick-graphite"),
    "okna-sfera": ("Окна Сфера", "Лидогенерирующие лендинги", "sky-yellow-graphite"),
    "chistiy-metr": ("Чистый метр", "Лидогенерирующие лендинги", "turquoise-lemon-dark"),
    "teplodom": ("ТеплоДом", "Лидогенерирующие лендинги", "red-green-gray"),
    "pereezd-prosto": ("Бережный переезд", "Лидогенерирующие лендинги", "cobalt-green-red"),
    "pravo-opora": ("Правовая опора", "Лидогенерирующие лендинги", "forest-gold-burgundy"),
    "sever-market": ("Северный маршрут", "Проекты посложнее", "pine-red-gray"),
    "modulprof": ("МодульПроф", "Проекты посложнее", "graphite-yellow-blue"),
    "doma-u-ozera": ("Дома у озера", "Проекты посложнее", "forest-berry"),
    "praktika": ("Практика", "Проекты посложнее", "coral-turquoise-black"),
    "gruzcontrol": ("ГрузКонтроль", "Проекты посложнее", "green-red-amber"),
}

_ROUTES = {
    "tochka-hoda": (("cover", "/"), ("diagnostics", "/uslugi/diagnostika-avtomobilya"), ("services", "/uslugi"), ("case-study", "/cases/bmw-x5"), ("prices", "/ceny")),
    "dentalea": (("cover", "/"), ("implantation", "/uslugi/implantatsiya-zubov"), ("doctors", "/vrachi"), ("case-study", "/cases/ulybka"), ("prices", "/ceny")),
    "ventkontur": (("cover", "/"), ("catalog", "/catalog/ventilyatsionnye-ustanovki"), ("selection", "/podbor-oborudovaniya"), ("projects", "/proekty"), ("service", "/servis")),
    "syr-hleb": (("cover", "/"), ("gift-sets", "/catalog/podarochnye-nabory"), ("cheese", "/catalog/syry"), ("bakery", "/pekarnya"), ("delivery", "/dostavka")),
    "kvadrat-remonta": (("cover", "/"), ("renovation", "/uslugi/remont-kvartir"), ("portfolio", "/portfolio"), ("calculator", "/kalkulyator-smety"), ("stages", "/etapy-rabot")),
    "okna-sfera": (("cover", "/"), ("windows", "/plastikovye-okna"), ("calculator", "/raschet-okna"), ("profiles", "/profili"), ("installation", "/montazh")),
    "chistiy-metr": (("cover", "/"), ("after-renovation", "/uborka-posle-remonta"), ("calculator", "/raschet-uborki"), ("checklist", "/chto-vhodit"), ("reviews", "/otzyvy")),
    "teplodom": (("cover", "/"), ("boiler-repair", "/remont-gazovyh-kotlov"), ("diagnostics", "/diagnostika-kotla"), ("prices", "/ceny"), ("request", "/vyzov-mastera")),
    "pereezd-prosto": (("cover", "/"), ("apartment-moving", "/kvartirnyy-pereezd"), ("calculator", "/raschet-pereezda"), ("packing", "/upakovka-veshchey"), ("route", "/marshrut")),
    "pravo-opora": (("cover", "/"), ("developer-disputes", "/uslugi/spory-s-zastroyshchikom"), ("assessment", "/otsenka-dela"), ("practice", "/sudebnaya-praktika"), ("consultation", "/konsultatsiya")),
    "sever-market": (("cover", "/"), ("catalog", "/catalog/turisticheskoe-snaryazhenie"), ("tents", "/catalog/palatki"), ("cart", "/korzina"), ("delivery", "/dostavka")),
    "modulprof": (("cover", "/"), ("catalog", "/catalog/modulnye-zdaniya"), ("configurator", "/konfigurator"), ("comparison", "/sravnenie-komplektatsiy"), ("projects", "/proekty")),
    "doma-u-ozera": (("cover", "/"), ("sauna-house", "/booking/dom-s-saunoy"), ("search", "/poisk-domov"), ("calendar", "/svobodnye-daty"), ("booking", "/bronirovanie")),
    "praktika": (("cover", "/"), ("courses", "/cabinet/courses"), ("curriculum", "/courses/web-design/program"), ("lesson", "/courses/web-design/lesson-4"), ("progress", "/cabinet/progress")),
    "gruzcontrol": (("cover", "/"), ("deliveries", "/dashboard/dostavki"), ("dispatch", "/dashboard/dispatch"), ("route", "/deliveries/GC-1842"), ("analytics", "/dashboard/analytics")),
}

_ASSET_KEYS = {
    "tochka-hoda": ("workshop_hero", "diagnostic_closeup", "mechanic_portrait", "bmw_before", "bmw_after", "service_lounge", "engine_inspection"),
    "dentalea": ("clinic_exterior", "doctor_portrait", "consultation_room", "smile_case_before", "smile_case_after", "treatment_detail"),
    "ventkontur": ("factory_rooftop", "air_handling_unit", "engineer_portrait", "duct_installation", "control_panel", "project_hall"),
    "syr-hleb": ("cheese_counter", "artisan_bread", "gift_box", "farmer_portrait", "tasting_table", "delivery_basket"),
    "kvadrat-remonta": ("living_room_before", "living_room_after", "designer_portrait", "material_samples", "kitchen_detail", "renovation_team"),
    "okna-sfera": ("window_facade", "profile_closeup", "installer_portrait", "bright_kitchen", "glazing_process", "balcony_view"),
    "chistiy-metr": ("clean_kitchen", "bathroom_detail", "cleaner_portrait", "before_cleanup", "after_cleanup", "equipment_case"),
    "teplodom": ("boiler_room", "technician_portrait", "burner_closeup", "diagnostic_tool", "repair_process", "warm_home"),
    "pereezd-prosto": ("moving_van", "packer_portrait", "packed_living_room", "boxes_detail", "route_map_photo", "new_home"),
    "pravo-opora": ("office_exterior", "lawyer_portrait", "consultation_table", "case_documents", "courtroom_hall", "client_meeting"),
    "sever-market": ("mountain_tent", "hiking_backpack", "campfire_scene", "gear_closeup", "guide_portrait", "winter_route"),
    "modulprof": ("modular_building", "factory_assembly", "architect_portrait", "interior_module", "site_installation", "facade_detail"),
    "doma-u-ozera": ("lakeside_house", "sauna_interior", "terrace_view", "host_portrait", "bedroom_detail", "evening_pier"),
    "praktika": ("student_workspace", "mentor_portrait", "lesson_notebook", "design_board", "team_review", "graduation_scene"),
    "gruzcontrol": ("logistics_terminal", "dispatcher_portrait", "truck_fleet", "warehouse_scan", "delivery_driver", "route_overview"),
}

_CATEGORY = ("Разработка и IT", "Создание сайта")


def _shots(slug: str) -> tuple[ShotSpec, ...]:
    return tuple(ShotSpec(key, path, "desktop", key) for key, path in _ROUTES[slug])


def _assets(slug: str, brand: str) -> tuple[AssetSpec, ...]:
    return tuple(
        AssetSpec(
            key=key,
            filename=f"{key.replace('_', '-')}.png",
            prompt=(
                f"Фотореалистичная предметная фотография для авторского "
                f"концепта сайта «{brand}»: {key.replace('_', ' ')}, "
                "без логотипов и текста"
            ),
        )
        for key in _ASSET_KEYS[slug]
    )


def _build_project(slug: str, domain: str, title: str) -> ProjectSpec:
    brand, group, palette = _PROJECT_DETAILS[slug]
    return ProjectSpec(
        slug=slug,
        brand=brand,
        kwork_title=title,
        group=group,
        domain=domain,
        category=_CATEGORY,
        work_type="Новый сайт",
        description=(
            f"Авторский концепт сайта «{brand}»: продуманная структура, "
            "интерфейс и сценарий для демонстрации проекта."
        ),
        palette=palette,
        renderer_module=f"portfolio.kwork_pack.sites.{slug.replace('-', '_')}",
        shots=_shots(slug),
        assets=_assets(slug, brand),
    )


PROJECTS: tuple[ProjectSpec, ...] = tuple(
    _build_project(slug, domain, title) for slug, domain, title in PROJECT_IDENTITIES
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
    path = shot.path if shot.path.startswith("/") else f"/{shot.path}"
    return f"https://{project.domain}{path}"
