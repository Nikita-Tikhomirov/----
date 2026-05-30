from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path

try:
    import browser_cookie3
except ImportError:  # pragma: no cover - dependency can be absent before install
    browser_cookie3 = None


logger = logging.getLogger(__name__)


def chrome_cookie_header(domain_name: str = ".kwork.ru") -> str:
    """Return a Cookie header from the current user's Chrome profile."""
    if browser_cookie3 is None:
        logger.warning("browser_cookie3 is not installed; cannot import Chrome cookies")
        return ""
    try:
        jar = browser_cookie3.chrome(domain_name=domain_name)
    except Exception as exc:
        logger.info("Direct Chrome cookie read failed for %s: %s", domain_name, exc)
        jar = _read_copied_chrome_cookie_jar(domain_name)
        if jar is None:
            logger.warning("Failed to read Chrome cookies for %s: %s", domain_name, exc)
            return ""
    pairs = sorted(f"{cookie.name}={cookie.value}" for cookie in jar if cookie.name and cookie.value)
    return "; ".join(pairs)


def _read_copied_chrome_cookie_jar(domain_name: str):
    for cookie_file, key_file in _default_chrome_cookie_files():
        copied_cookie = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
                copied_cookie = Path(tmp.name)
            shutil.copy2(cookie_file, copied_cookie)
            return browser_cookie3.chrome(
                cookie_file=str(copied_cookie),
                key_file=str(key_file),
                domain_name=domain_name,
            )
        except Exception as exc:
            logger.info("Copied Chrome cookie read failed for %s: %s", cookie_file, exc)
        finally:
            if copied_cookie is not None:
                copied_cookie.unlink(missing_ok=True)
    return None


def _default_chrome_cookie_files() -> list[tuple[Path, Path]]:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    if not local_app_data:
        return []
    user_data = local_app_data / "Google" / "Chrome" / "User Data"
    local_state = user_data / "Local State"
    candidates: list[tuple[Path, Path]] = []
    for profile in ("Default", "Profile 1", "Profile 2", "Profile 3"):
        profile_dir = user_data / profile
        for relative in (Path("Network") / "Cookies", Path("Cookies")):
            cookie_file = profile_dir / relative
            if cookie_file.exists() and local_state.exists():
                candidates.append((cookie_file, local_state))
    return candidates
