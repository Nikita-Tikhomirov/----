from html import escape


_ICON_NODES = {
    "lock": (
        '<rect width="18" height="11" x="3" y="11" rx="2" ry="2" />',
        '<path d="M7 11V7a5 5 0 0 1 10 0v4" />',
    ),
    "arrow-right": (
        '<path d="M5 12h14" />',
        '<path d="m12 5 7 7-7 7" />',
    ),
    "phone": (
        '<path d="M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384" />',
    ),
    "calendar": (
        '<path d="M8 2v3" />',
        '<path d="M16 2v3" />',
        '<rect x="3" y="3" width="18" height="18" rx="2" />',
        '<path d="M3 9h18" />',
    ),
    "shopping-cart": (
        '<circle cx="8" cy="21" r="1" />',
        '<circle cx="19" cy="21" r="1" />',
        '<path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12" />',
    ),
    "filter": (
        '<path d="M10 20a1 1 0 0 0 .553.895l2 1A1 1 0 0 0 14 21v-7a2 2 0 0 1 .517-1.341L21.74 4.67A1 1 0 0 0 21 3H3a1 1 0 0 0-.742 1.67l7.225 7.989A2 2 0 0 1 10 14z" />',
    ),
    "check": (
        '<path d="M20 6 9 17l-5-5" />',
    ),
    "map-pin": (
        '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />',
        '<circle cx="12" cy="10" r="3" />',
    ),
}


def icon(name: str, *, size: int = 20) -> str:
    """Return a small inline Lucide SVG by its catalog name."""
    try:
        nodes = _ICON_NODES[name]
    except KeyError as exc:
        raise KeyError(f"unknown icon: {name}") from exc

    dimension = escape(str(int(size)), quote=True)
    return (
        f'<svg class="lucide-icon" xmlns="http://www.w3.org/2000/svg" '
        f'width="{dimension}" height="{dimension}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{"".join(nodes)}</svg>'
    )
