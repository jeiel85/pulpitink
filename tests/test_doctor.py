from sermonscript.services.diagnostics import run_doctor


def test_doctor_returns_report_with_expected_checks():
    report = run_doctor()
    names = [item.name for item in report.results]
    assert "Python 버전" in names
    assert "운영체제" in names
    assert "FFmpeg" in names
    assert "작업 디렉터리 쓰기 권한" in names
    assert "앱 데이터 디렉터리" in names


def test_doctor_failed_items_have_hint():
    report = run_doctor()
    for item in report.results:
        if not item.ok:
            assert item.hint, f"실패 항목 '{item.name}'에 해결 힌트가 없습니다."


def test_doctor_python_check_passes_on_supported_runtime():
    report = run_doctor()
    python = next(item for item in report.results if item.name == "Python 버전")
    assert python.ok
