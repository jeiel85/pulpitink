import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from pulpit_ink.core.utils.update_checker import (
    CACHE_FILE_NAME,
    check_for_updates,
    is_new_version_available,
    parse_version,
)


def test_parse_version():
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("  v2.0.1-alpha.3  ") == (2, 0, 1)
    assert parse_version("v3.4.5+build.123") == (3, 4, 5)
    assert parse_version("v4.5") == (4, 5, 0)
    assert parse_version("invalid") == (0, 0, 0)


def test_is_new_version_available():
    assert is_new_version_available("v1.0.0", "v1.0.1") is True
    assert is_new_version_available("v1.0.0", "v2.0.0") is True
    assert is_new_version_available("v1.2.3", "v1.2.3") is False
    assert is_new_version_available("v1.2.3", "v1.2.2") is False


def _create_mock_response(tag_name: str, html_url: str) -> MagicMock:
    mock_resp = MagicMock()
    data = {"tag_name": tag_name, "html_url": html_url}
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    return mock_resp


@patch("urllib.request.urlopen")
def test_check_for_updates_new_version(mock_urlopen, tmp_path):
    # Mock AppPaths to write cache to tmp_path
    mock_paths = MagicMock()
    mock_paths.ensure.return_value = mock_paths
    mock_paths.data_dir = tmp_path

    with patch("pulpit_ink.core.utils.update_checker.get_app_paths", return_value=mock_paths):
        mock_urlopen.return_value = _create_mock_response("v1.2.0", "https://example.com/dl")

        # Current version is lower -> has_update=True
        has_up, latest, dl, err = check_for_updates("v1.0.0")

        assert has_up is True
        assert latest == "v1.2.0"
        assert dl == "https://example.com/dl"
        assert err is None
        assert mock_urlopen.call_count == 1

        # Check if cache file is written
        cache_file = tmp_path / CACHE_FILE_NAME
        assert cache_file.exists()


@patch("urllib.request.urlopen")
def test_check_for_updates_no_new_version(mock_urlopen, tmp_path):
    mock_paths = MagicMock()
    mock_paths.ensure.return_value = mock_paths
    mock_paths.data_dir = tmp_path

    with patch("pulpit_ink.core.utils.update_checker.get_app_paths", return_value=mock_paths):
        mock_urlopen.return_value = _create_mock_response("v1.0.0", "https://example.com/dl")

        # Current version is equal -> has_update=False
        has_up, latest, dl, err = check_for_updates("v1.0.0")

        assert has_up is False
        assert latest == "v1.0.0"
        assert err is None


@patch("urllib.request.urlopen")
def test_check_for_updates_network_failure(mock_urlopen, tmp_path):
    mock_paths = MagicMock()
    mock_paths.ensure.return_value = mock_paths
    mock_paths.data_dir = tmp_path

    with patch("pulpit_ink.core.utils.update_checker.get_app_paths", return_value=mock_paths):
        # Simulate network error
        mock_urlopen.side_effect = Exception("Timeout connecting to API")

        # Must fall back gracefully (has_update=False, empty info, error message returned)
        has_up, latest, dl, err = check_for_updates("v1.0.0")

        assert has_up is False
        assert latest == ""
        assert dl == ""
        assert "Timeout connecting to API" in err


@patch("urllib.request.urlopen")
def test_check_for_updates_caching_24h(mock_urlopen, tmp_path):
    mock_paths = MagicMock()
    mock_paths.ensure.return_value = mock_paths
    mock_paths.data_dir = tmp_path

    with patch("pulpit_ink.core.utils.update_checker.get_app_paths", return_value=mock_paths):
        # 1. Populate cache with checked time 5 hours ago
        cache_file = tmp_path / CACHE_FILE_NAME
        checked_time = datetime.now(UTC) - timedelta(hours=5)

        cache_data = {
            "last_checked_at": checked_time.isoformat(),
            "latest_version": "v1.5.0",
            "download_url": "https://example.com/cached",
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # 2. Trigger check
        # Since it is within 24 hours, urlopen must NOT be called
        has_up, latest, dl, err = check_for_updates("v1.0.0", force=False)

        assert has_up is True
        assert latest == "v1.5.0"
        assert dl == "https://example.com/cached"
        assert err is None
        mock_urlopen.assert_not_called()


@patch("urllib.request.urlopen")
def test_check_for_updates_cache_expired(mock_urlopen, tmp_path):
    mock_paths = MagicMock()
    mock_paths.ensure.return_value = mock_paths
    mock_paths.data_dir = tmp_path

    with patch("pulpit_ink.core.utils.update_checker.get_app_paths", return_value=mock_paths):
        # 1. Populate cache with checked time 25 hours ago
        cache_file = tmp_path / CACHE_FILE_NAME
        checked_time = datetime.now(UTC) - timedelta(hours=25)

        cache_data = {
            "last_checked_at": checked_time.isoformat(),
            "latest_version": "v1.5.0",
            "download_url": "https://example.com/cached",
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # 2. Trigger check (since > 24 hours, it must call URL)
        mock_urlopen.return_value = _create_mock_response("v1.6.0", "https://example.com/new")

        has_up, latest, dl, err = check_for_updates("v1.0.0", force=False)

        assert has_up is True
        assert latest == "v1.6.0"
        assert dl == "https://example.com/new"
        assert err is None
        assert mock_urlopen.call_count == 1

        # Check if cache is updated
        with open(cache_file, encoding="utf-8") as f:
            updated_cache = json.load(f)
        assert updated_cache["latest_version"] == "v1.6.0"


@patch("urllib.request.urlopen")
def test_check_for_updates_forced_bypass(mock_urlopen, tmp_path):
    mock_paths = MagicMock()
    mock_paths.ensure.return_value = mock_paths
    mock_paths.data_dir = tmp_path

    with patch("pulpit_ink.core.utils.update_checker.get_app_paths", return_value=mock_paths):
        # 1. Populate cache with checked time 1 hour ago
        cache_file = tmp_path / CACHE_FILE_NAME
        checked_time = datetime.now(UTC) - timedelta(hours=1)

        cache_data = {
            "last_checked_at": checked_time.isoformat(),
            "latest_version": "v1.5.0",
            "download_url": "https://example.com/cached",
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # 2. Trigger forced check (force=True)
        # Even within 24 hours, it must bypass cache and query API
        mock_urlopen.return_value = _create_mock_response("v1.7.0", "https://example.com/forced")

        has_up, latest, dl, err = check_for_updates("v1.0.0", force=True)

        assert has_up is True
        assert latest == "v1.7.0"
        assert dl == "https://example.com/forced"
        assert err is None
        assert mock_urlopen.call_count == 1

        # Check if cache is updated
        with open(cache_file, encoding="utf-8") as f:
            updated_cache = json.load(f)
        assert updated_cache["latest_version"] == "v1.7.0"
