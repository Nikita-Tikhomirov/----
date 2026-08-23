import socket
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class DomainStatus:
    domain: str
    resolves: bool
    addresses: tuple[str, ...]


def check_domain(
    domain: str,
    resolver: Callable[..., object] = socket.getaddrinfo,
) -> DomainStatus:
    """Resolve a concept domain, treating any returned address as a collision."""
    try:
        results = resolver(domain, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return DomainStatus(domain, False, ())

    addresses = tuple(
        dict.fromkeys(str(result[4][0]) for result in results)  # type: ignore[index]
    )
    return DomainStatus(domain, bool(addresses), addresses)
