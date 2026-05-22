"""Tests for the Tauri/IPC helper CLI commands.

Covers ``pulpit-ink user-dict``, ``pulpit-ink update-check`` and
``pulpit-ink youtube check`` JSON outputs the React shell depends on.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from pulpit_ink.cli.main import app

runner = CliRunner()


def test_user_dict_list_empty(tmp_path: Path) -> None:
    target = tmp_path / "missing.json"
    result = runner.invoke(app, ["user-dict", "list", "--path", str(target), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["path"] == str(target)
    assert payload["entries"] == {}


def test_user_dict_add_then_list(tmp_path: Path) -> None:
    target = tmp_path / "user_dict.json"
    add_result = runner.invoke(
        app,
        ["user-dict", "add", "예수 그리스도", "이에수", "예수그리스도", "--path", str(target), "--json"],
    )
    assert add_result.exit_code == 0, add_result.stdout
    add_payload = json.loads(add_result.stdout)
    assert add_payload["ok"] is True
    assert add_payload["wrong_forms"] == ["이에수", "예수그리스도"]

    list_result = runner.invoke(app, ["user-dict", "list", "--path", str(target), "--json"])
    assert list_result.exit_code == 0
    list_payload = json.loads(list_result.stdout)
    assert list_payload["entries"]["예수 그리스도"] == ["이에수", "예수그리스도"]


def test_user_dict_remove(tmp_path: Path) -> None:
    target = tmp_path / "user_dict.json"
    runner.invoke(app, ["user-dict", "add", "은혜", "--path", str(target), "--json"])
    remove_result = runner.invoke(
        app, ["user-dict", "remove", "은혜", "--path", str(target), "--json"]
    )
    assert remove_result.exit_code == 0
    payload = json.loads(remove_result.stdout)
    assert payload["ok"] is True
    list_payload = json.loads(
        runner.invoke(app, ["user-dict", "list", "--path", str(target), "--json"]).stdout
    )
    assert "은혜" not in list_payload["entries"]


def test_user_dict_import_export_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "user_dict.json"
    csv_in = tmp_path / "in.csv"
    csv_in.write_text(
        "예수 그리스도,이에수,예수그리스도\n복음,보궁\n", encoding="utf-8"
    )

    import_result = runner.invoke(
        app, ["user-dict", "import", str(csv_in), "--path", str(target), "--json"]
    )
    assert import_result.exit_code == 0
    import_payload = json.loads(import_result.stdout)
    assert import_payload["imported"] == 2
    assert import_payload["total"] == 2

    csv_out = tmp_path / "out.csv"
    export_result = runner.invoke(
        app, ["user-dict", "export", str(csv_out), "--path", str(target), "--json"]
    )
    assert export_result.exit_code == 0
    export_payload = json.loads(export_result.stdout)
    assert export_payload["exported"] == 2
    text = csv_out.read_text(encoding="utf-8")
    assert "예수 그리스도" in text
    assert "이에수" in text


def test_update_check_json(tmp_path: Path) -> None:
    with patch(
        "pulpit_ink.cli.main.check_for_updates",
        return_value=(True, "v9.9.9", "https://example.com/release", None),
    ):
        result = runner.invoke(app, ["update-check", "--json", "--current", "v0.4.7"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["has_update"] is True
    assert payload["latest_version"] == "v9.9.9"
    assert payload["current_version"] == "v0.4.7"
    assert payload["error"] is None


def test_youtube_check_json_available() -> None:
    with patch("pulpit_ink.cli.main.is_yt_dlp_available", return_value=True):
        result = runner.invoke(app, ["youtube", "check", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["available"] is True


def test_youtube_check_json_missing() -> None:
    with patch("pulpit_ink.cli.main.is_yt_dlp_available", return_value=False):
        result = runner.invoke(app, ["youtube", "check", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["available"] is False


def test_youtube_install_already_installed() -> None:
    with patch("pulpit_ink.cli.main.is_yt_dlp_available", return_value=True):
        result = runner.invoke(app, ["youtube", "install", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["already"] is True
