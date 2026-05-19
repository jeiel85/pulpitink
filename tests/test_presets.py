from sermonscript.core.audio.enhancement_presets import PRESETS


def test_required_presets_exist():
    assert {"none", "stt_basic", "sermon", "noisy"}.issubset(PRESETS.keys())


def test_sermon_preset_uses_mono_16khz():
    preset = PRESETS["sermon"]
    assert preset.channels == 1
    assert preset.sample_rate == 16000
