import socket

import pytest

import portfolio.kwork_pack.cli as cli
from portfolio.kwork_pack.catalog import PROJECTS
from portfolio.kwork_pack.domain_check import DomainStatus, check_domain


def test_resolved_domain_is_treated_as_a_collision():
    def resolver(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.10", 0))]

    status = check_domain("tochka-hoda.ru", resolver=resolver)
    assert status.resolves is True
    assert status.addresses == ("203.0.113.10",)


def test_unresolved_domain_is_available_for_a_concept():
    def resolver(*_args, **_kwargs):
        raise socket.gaierror("not found")

    status = check_domain("tochka-hoda.ru", resolver=resolver)
    assert status.resolves is False
    assert status.addresses == ()


def test_domain_check_deduplicates_ipv4_and_ipv6_in_resolver_order():
    def resolver(*_args, **_kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.10", 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 0, 0, 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("203.0.113.10", 0)),
        ]

    status = check_domain("tochka-hoda.ru", resolver=resolver)

    assert status.addresses == ("203.0.113.10", "2001:db8::1")


def test_domain_check_surfaces_non_dns_errors():
    def resolver(*_args, **_kwargs):
        raise RuntimeError("resolver unavailable")

    with pytest.raises(RuntimeError, match="resolver unavailable"):
        check_domain("tochka-hoda.ru", resolver=resolver)


def test_domains_cli_uses_injected_statuses_without_live_dns(
    monkeypatch, capsys
):
    projects = PROJECTS[:2]

    def fake_check_domain(domain):
        if domain == projects[0].domain:
            return DomainStatus(domain, True, ("203.0.113.10",))
        return DomainStatus(domain, False, ())

    monkeypatch.setattr(cli, "PROJECTS", projects)
    monkeypatch.setattr(cli, "check_domain", fake_check_domain)

    assert cli.main(["domains", "--check"]) == 1

    output = capsys.readouterr().out
    assert "коллизия" in output.lower()
    assert "DNS-записей нет" in output
    assert "203.0.113.10" in output
