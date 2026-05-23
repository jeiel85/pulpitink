"""GitHub Releases API based Update Checker with 24-hour local caching.

Uses pure Python standard library to minimize dependency weight and security risk.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

from pulpit_ink.app.paths import get_app_paths

logger = logging.getLogger("pulpit_ink.utils.update_checker")

GITHUB_API_URL = "https://api.github.com/repos/jeiel85/pulpit-ink-desktop/releases/latest"
CACHE_FILE_NAME = "update_cache.json"


def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a semantic version string into a (major, minor, patch) integer tuple.

    Strips common prefixes, prerelease tags, and build metadata safely.
    E.g., "v1.2.3-alpha+build.4" -> (1, 2, 3).
    """
    # Remove 'v' or 'V' prefixes and whitespace
    clean = version_str.strip().lower()
    if clean.startswith("v"):
        clean = clean[1:]

    # Remove prerelease identifiers (everything after '-')
    if "-" in clean:
        clean = clean.split("-", 1)[0]

    # Remove build metadata (everything after '+')
    if "+" in clean:
        clean = clean.split("+", 1)[0]

    parts = clean.split(".")
    major = 0
    minor = 0
    patch = 0

    try:
        if len(parts) >= 1:
            major = int(parts[0])
        if len(parts) >= 2:
            minor = int(parts[1])
        if len(parts) >= 3:
            patch = int(parts[2])
    except ValueError:
        logger.warning("Failed to parse version components from '%s'", version_str)

    return (major, minor, patch)


def is_new_version_available(current: str, latest: str) -> bool:
    """Compare two version strings using semantic version components."""
    curr_tup = parse_version(current)
    late_tup = parse_version(latest)
    return late_tup > curr_tup


def check_for_updates(
    current_version: str, force: bool = False
) -> tuple[bool, str, str, str | None]:
    """Check GitHub Releases for updates.

    Returns:
        (has_update, latest_version, download_url, error_message)
    """
    cache_path = get_app_paths().ensure().data_dir / CACHE_FILE_NAME
    now = datetime.now(UTC)

    # 1. Try to read from cache if not forced
    if not force and cache_path.exists():
        try:
            with open(cache_path, encoding="utf-8") as f:
                cache = json.load(f)

            last_checked_str = cache.get("last_checked_at")
            if last_checked_str:
                last_checked = datetime.fromisoformat(last_checked_str)
                # If checked within the last 24 hours, use cached data
                if now - last_checked < timedelta(hours=24):
                    logger.info("Using cached update check results (checked within 24 hours)")
                    latest_ver = cache.get("latest_version", "")
                    dl_url = cache.get("download_url", "")
                    has_up = is_new_version_available(current_version, latest_ver)
                    return has_up, latest_ver, dl_url, None
        except Exception as exc:
            logger.warning("Failed to read update cache: %s", exc)

    # 2. Fetch from GitHub API
    logger.info("Fetching latest release information from GitHub API: %s", GITHUB_API_URL)
    req = urllib.request.Request(
        GITHUB_API_URL,
        headers={
            "User-Agent": f"PulpitInk-Update-Checker/v{current_version}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=5.0) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_version = data.get("tag_name", "").strip()
            download_url = data.get("html_url", "").strip()

            if not latest_version:
                raise ValueError("tag_name not found in GitHub API response")
            if not download_url:
                # Fallback URL
                download_url = "https://github.com/jeiel85/pulpit-ink-desktop/releases"

            has_update = is_new_version_available(current_version, latest_version)

            # Write to cache
            try:
                cache_data = {
                    "last_checked_at": now.isoformat(),
                    "latest_version": latest_version,
                    "download_url": download_url,
                }
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            except Exception as exc:
                logger.warning("Failed to write update cache: %s", exc)

            return has_update, latest_version, download_url, None

    except urllib.error.HTTPError as exc:
        err_msg = f"HTTP Error {exc.code}: {exc.reason}"
        logger.warning("GitHub API request failed: %s", err_msg)
        return False, "", "", err_msg
    except urllib.error.URLError as exc:
        err_msg = f"Network Connection Error: {exc.reason}"
        logger.warning("GitHub API request failed: %s", err_msg)
        return False, "", "", err_msg
    except Exception as exc:
        err_msg = str(exc)
        logger.warning("Unexpected error during update check: %s", err_msg)
        return False, "", "", err_msg
