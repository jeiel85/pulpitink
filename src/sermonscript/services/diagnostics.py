"""``sermonscript doctor`` business logic.

Kept separate from the CLI presentation so it can be unit-tested and reused
by the future GUI.
"""

from __future__ import annotations

import platform
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from sermonscript.app.paths import get_app_paths
from sermonscript.core.audio.ffmpeg_runner import FFmpegRunner


@dataclass(frozen=True)
class DoctorResult:
    name: str
    ok: bool
    detail: str
    hint: str | None = None


@dataclass
class DoctorReport:
    results: list[DoctorResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    def add(self, result: DoctorResult) -> None:
        self.results.append(result)


def _check_python() -> DoctorResult:
    version = sys.version.split()[0]
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 11):
        return DoctorResult("Python 버전", True, f"Python {version} 사용 중")
    return DoctorResult(
        "Python 버전",
        False,
        f"현재 Python {version}",
        hint="Python 3.11 이상이 필요합니다. 새로운 Python을 설치한 뒤 가상 환경을 다시 만들어 주세요.",
    )


def _check_os() -> DoctorResult:
    info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    return DoctorResult("운영체제", True, info)


def _check_ffmpeg() -> DoctorResult:
    check = FFmpegRunner().check()
    if check.available:
        detail = f"발견: {check.executable}"
        if check.version_line:
            detail += f" / {check.version_line}"
        return DoctorResult("FFmpeg", True, detail)
    return DoctorResult(
        "FFmpeg",
        False,
        check.error or "FFmpeg을 찾을 수 없습니다.",
        hint=(
            "https://ffmpeg.org 에서 설치 후 PATH에 등록하거나 "
            "winget install Gyan.FFmpeg 같은 패키지 매니저를 사용하세요."
        ),
    )


def _check_cwd_writable() -> DoctorResult:
    cwd = Path.cwd()
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            prefix=".sermonscript_write_test_",
            dir=cwd,
            delete=True,
            encoding="utf-8",
        ) as fh:
            fh.write("ok")
    except OSError as exc:
        return DoctorResult(
            "작업 디렉터리 쓰기 권한",
            False,
            f"현재 디렉터리({cwd})에 쓸 수 없습니다: {exc}",
            hint="권한이 있는 디렉터리에서 실행하거나 관리자 권한으로 다시 시도하세요.",
        )
    return DoctorResult("작업 디렉터리 쓰기 권한", True, f"쓰기 가능 ({cwd})")


def _check_app_data_dir() -> DoctorResult:
    paths = get_app_paths()
    try:
        paths.ensure()
        probe = paths.data_dir / ".sermonscript_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        return DoctorResult(
            "앱 데이터 디렉터리",
            False,
            f"{paths.data_dir} 에 쓸 수 없습니다: {exc}",
            hint="사용자 데이터 디렉터리 권한을 확인하거나 다른 사용자 계정으로 실행해 보세요.",
        )
    return DoctorResult(
        "앱 데이터 디렉터리",
        True,
        f"준비 완료 (data: {paths.data_dir}, cache: {paths.cache_dir})",
    )


def run_doctor() -> DoctorReport:
    """Run all environment checks and return a structured report."""

    report = DoctorReport()
    report.add(_check_python())
    report.add(_check_os())
    report.add(_check_ffmpeg())
    report.add(_check_cwd_writable())
    report.add(_check_app_data_dir())
    return report
