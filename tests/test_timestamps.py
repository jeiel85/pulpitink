from sermonscript.core.export.timestamps import (
    format_srt_timestamp,
    format_vtt_timestamp,
)


def test_srt_zero():
    assert format_srt_timestamp(0) == "00:00:00,000"


def test_vtt_zero():
    assert format_vtt_timestamp(0) == "00:00:00.000"


def test_srt_basic_seconds():
    assert format_srt_timestamp(5.3) == "00:00:05,300"


def test_vtt_basic_seconds():
    assert format_vtt_timestamp(5.3) == "00:00:05.300"


def test_srt_minutes_and_hours():
    # 1h 2m 3.456s
    seconds = 3600 + 2 * 60 + 3.456
    assert format_srt_timestamp(seconds) == "01:02:03,456"


def test_vtt_minutes_and_hours():
    seconds = 3600 + 2 * 60 + 3.456
    assert format_vtt_timestamp(seconds) == "01:02:03.456"


def test_negative_clamped_to_zero():
    assert format_srt_timestamp(-1.0) == "00:00:00,000"
    assert format_vtt_timestamp(-1.0) == "00:00:00.000"


def test_millisecond_rounding():
    # round-half-to-even on the millisecond boundary; we just check stable formatting
    assert format_srt_timestamp(1.2349) == "00:00:01,235"
    assert format_vtt_timestamp(1.2349) == "00:00:01.235"
    assert format_srt_timestamp(0.999) == "00:00:00,999"
    assert format_vtt_timestamp(0.999) == "00:00:00.999"
