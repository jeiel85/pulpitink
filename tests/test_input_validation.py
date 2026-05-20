from pathlib import Path

import pytest

from sermonscript.app.exceptions import SermonScriptError, UnsupportedFormatError
from sermonscript.services.transcribe_service import (
    SUPPORTED_INPUT_EXTENSIONS,
    validate_input_path,
)


def test_supported_extensions_match_spec():
    assert SUPPORTED_INPUT_EXTENSIONS == frozenset(
        {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp4"}
    )


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(SermonScriptError):
        validate_input_path(tmp_path / "missing.mp3")


def test_unsupported_extension_raises(tmp_path: Path):
    bogus = tmp_path / "notes.txt"
    bogus.write_text("hello")
    with pytest.raises(UnsupportedFormatError):
        validate_input_path(bogus)


def test_directory_not_accepted(tmp_path: Path):
    with pytest.raises(SermonScriptError):
        validate_input_path(tmp_path)


def test_valid_extension_resolves(tmp_path: Path):
    sample = tmp_path / "sermon.mp3"
    sample.write_bytes(b"")
    resolved = validate_input_path(sample)
    assert resolved.suffix == ".mp3"
    assert resolved.is_absolute()
