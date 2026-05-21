import pytest

from pulpit_ink.app.exceptions import PulpitInkError
from pulpit_ink.core.audio.enhancement_presets import (
    PRESETS,
    build_ffmpeg_filter,
    get_preset,
)


def test_required_presets_exist():
    assert {"none", "stt_basic", "sermon", "noisy"}.issubset(PRESETS.keys())


def test_sermon_preset_uses_mono_16khz():
    preset = PRESETS["sermon"]
    assert preset.channels == 1
    assert preset.sample_rate == 16000


def test_stt_basic_filter_contains_expected_filters():
    fl = build_ffmpeg_filter("stt_basic")
    assert "highpass=f=80" in fl
    assert "lowpass=f=7800" in fl
    assert "loudnorm" in fl


def test_sermon_filter_includes_denoise_and_dynaudnorm():
    fl = build_ffmpeg_filter("sermon")
    assert "afftdn" in fl
    assert "dynaudnorm" in fl
    assert "loudnorm" in fl


def test_noisy_preset_uses_stronger_highpass():
    assert "highpass=f=100" in build_ffmpeg_filter("noisy")


def test_none_preset_is_minimal():
    assert build_ffmpeg_filter("none") == "anull"


def test_unknown_preset_raises():
    with pytest.raises(PulpitInkError):
        get_preset("does-not-exist")
