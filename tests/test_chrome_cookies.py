from http.cookiejar import Cookie, CookieJar

from app.chrome_cookies import chrome_cookie_header, _default_chrome_cookie_files


def _cookie(name: str, value: str, domain: str = ".kwork.ru") -> Cookie:
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=domain.startswith("."),
        path="/",
        path_specified=True,
        secure=True,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )


def test_chrome_cookie_header_formats_kwork_cookies(monkeypatch):
    jar = CookieJar()
    jar.set_cookie(_cookie("session", "abc"))
    jar.set_cookie(_cookie("other", "123"))

    class FakeBrowserCookie3:
        @staticmethod
        def chrome(domain_name):
            assert domain_name == ".kwork.ru"
            return jar

    monkeypatch.setattr("app.chrome_cookies.browser_cookie3", FakeBrowserCookie3)

    assert chrome_cookie_header(".kwork.ru") == "other=123; session=abc"


def test_chrome_cookie_header_returns_empty_when_reader_unavailable(monkeypatch):
    monkeypatch.setattr("app.chrome_cookies.browser_cookie3", None)

    assert chrome_cookie_header(".kwork.ru") == ""


def test_chrome_cookie_header_falls_back_to_copied_cookie_db(monkeypatch, tmp_path):
    source_cookie = tmp_path / "Cookies"
    source_key = tmp_path / "Local State"
    source_cookie.write_bytes(b"sqlite")
    source_key.write_text("{}", encoding="utf-8")
    jar = CookieJar()
    jar.set_cookie(_cookie("session", "abc"))
    calls = []

    class FakeBrowserCookie3:
        @staticmethod
        def chrome(cookie_file=None, domain_name="", key_file=None):
            calls.append((cookie_file, domain_name, key_file))
            if cookie_file is None:
                raise RuntimeError("This operation requires admin")
            assert cookie_file != str(source_cookie)
            assert key_file == str(source_key)
            return jar

    monkeypatch.setattr("app.chrome_cookies.browser_cookie3", FakeBrowserCookie3)
    monkeypatch.setattr(
        "app.chrome_cookies._default_chrome_cookie_files",
        lambda: [(source_cookie, source_key)],
    )

    assert chrome_cookie_header(".kwork.ru") == "session=abc"
    assert calls[0] == (None, ".kwork.ru", None)
    assert calls[1][1] == ".kwork.ru"


def test_default_chrome_cookie_files_prefers_network_cookie_db(monkeypatch, tmp_path):
    user_data = tmp_path / "Google" / "Chrome" / "User Data"
    network_cookie = user_data / "Default" / "Network" / "Cookies"
    local_state = user_data / "Local State"
    network_cookie.parent.mkdir(parents=True)
    network_cookie.write_bytes(b"sqlite")
    local_state.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert _default_chrome_cookie_files()[0] == (network_cookie, local_state)
