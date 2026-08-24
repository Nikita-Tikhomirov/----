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
    "car-front": (
        '<path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.65 5h-7.3A2 2 0 0 0 6.5 6.3L5 10 3 8" />',
        '<path d="M7 14h.01" />',
        '<path d="M17 14h.01" />',
        '<rect width="18" height="8" x="3" y="10" rx="2" />',
        '<path d="M5 18v2" />',
        '<path d="M19 18v2" />',
    ),
    "shield-check": (
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />',
        '<path d="m9 12 2 2 4-4" />',
    ),
    "settings": (
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />',
        '<circle cx="12" cy="12" r="3" />',
    ),
    "users": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />',
        '<circle cx="9" cy="7" r="4" />',
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87" />',
        '<path d="M16 3.13a4 4 0 0 1 0 7.75" />',
    ),
    "thumbs-up": (
        '<path d="M7 10v12" />',
        '<path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z" />',
    ),
    "clock": (
        '<circle cx="12" cy="12" r="10" />',
        '<polyline points="12 6 12 12 16 14" />',
    ),
    "wrench": (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94z" />',
    ),
    "activity": (
        '<path d="M22 12h-4l-3 9L9 3l-3 9H2" />',
    ),
    "chevron-down": (
        '<path d="m6 9 6 6 6-6" />',
    ),
    "message-circle": (
        '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z" />',
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
