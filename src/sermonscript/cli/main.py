"""SermonScript CLI entry point.

Built on Typer. Keep the CLI thin — orchestrate ``sermonscript.services``
modules so the same code can be reused from the future PySide6 GUI.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sermonscript import __version__
from sermonscript.app.exceptions import SermonScriptError
from sermonscript.app.logging_config import configure_logging
from sermonscript.core.audio.enhancement_presets import PRESETS
from sermonscript.core.audio.ffmpeg_runner import DEFAULT_PRESET
from sermonscript.core.export.base import ExportFormat
from sermonscript.services.diagnostics import DoctorReport, run_doctor
from sermonscript.services.transcribe_service import (
    TranscribeRequest,
    run_transcribe,
)

app = typer.Typer(
    help="SermonScript: 로컬 설교/강의 녹음 STT 도구",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _print_doctor_report(report: DoctorReport) -> None:
    table = Table(title="SermonScript 환경 진단", show_lines=False)
    table.add_column("항목", style="bold")
    table.add_column("상태")
    table.add_column("내용")

    for item in report.results:
        status = "[green]OK[/green]" if item.ok else "[red]실패[/red]"
        table.add_row(item.name, status, item.detail)

    console.print(table)

    failed = [item for item in report.results if not item.ok]
    if failed:
        console.print()
        console.print("[bold red]해결 힌트[/bold red]")
        for item in failed:
            if item.hint:
                console.print(f"- [yellow]{item.name}[/yellow]: {item.hint}")
            else:
                console.print(f"- [yellow]{item.name}[/yellow]: 추가 정보 없음")


@app.callback()
def _root(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="디버그 로그를 출력합니다."),
) -> None:
    """공통 옵션을 초기화합니다."""

    import logging

    configure_logging(level=logging.DEBUG if verbose else logging.INFO)


@app.command()
def version() -> None:
    """현재 SermonScript 버전을 출력합니다."""

    console.print(f"SermonScript {__version__}")


@app.command()
def doctor() -> None:
    """현재 환경이 SermonScript 실행에 적합한지 확인합니다."""

    report = run_doctor()
    _print_doctor_report(report)
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def presets() -> None:
    """사용 가능한 오디오 전처리 프리셋을 표시합니다."""

    table = Table(title="오디오 전처리 프리셋")
    table.add_column("이름", style="bold")
    table.add_column("샘플레이트")
    table.add_column("채널")
    table.add_column("설명")
    for preset in PRESETS.values():
        table.add_row(
            preset.name,
            f"{preset.sample_rate}Hz",
            str(preset.channels),
            preset.description,
        )
    console.print(table)


def _parse_formats(value: str) -> tuple[ExportFormat, ...]:
    items: list[ExportFormat] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        items.append(ExportFormat.parse(raw))
    if not items:
        raise typer.BadParameter("--format에 최소 한 가지 포맷이 필요합니다.")
    # de-duplicate while preserving order
    return tuple(dict.fromkeys(items))


@app.command()
def transcribe(
    input_path: Path = typer.Argument(..., help="변환할 오디오/비디오 파일 경로"),
    language: str = typer.Option("ko", "--language", "-l", help="언어 코드 (예: ko, en)"),
    model: str = typer.Option(
        "small", "--model", "-m", help="faster-whisper 모델 이름 (tiny|base|small|medium|large-v3)"
    ),
    preset: str = typer.Option(
        DEFAULT_PRESET, "--preset", help="오디오 전처리 프리셋 (none|stt_basic|sermon|noisy)"
    ),
    output: Path = typer.Option(
        Path("./exports"), "--output", "-o", help="변환 결과를 저장할 디렉터리"
    ),
    fmt: str = typer.Option(
        "txt,json,md,srt,vtt",
        "--format",
        "-f",
        help="콤마로 구분된 출력 포맷 목록",
    ),
    device: str = typer.Option("auto", "--device", help="STT 디바이스 (auto|cpu|cuda)"),
    compute_type: str = typer.Option(
        "int8", "--compute-type", help="faster-whisper compute_type (예: int8, float16)"
    ),
    beam_size: int = typer.Option(5, "--beam-size", help="STT beam size"),
    no_vad: bool = typer.Option(False, "--no-vad", help="VAD 필터를 끕니다."),
    initial_prompt: str | None = typer.Option(
        None, "--initial-prompt", help="STT 초기 프롬프트 (선택)"
    ),
    cache_root: Path = typer.Option(
        Path("cache") / "jobs",
        "--cache-root",
        help="전처리 결과(processed.wav)를 저장할 cache/jobs 경로",
    ),
) -> None:
    """로컬 오디오 파일을 전처리 → STT → Export 파이프라인으로 변환합니다."""

    formats = _parse_formats(fmt)

    request = TranscribeRequest(
        input_path=input_path,
        output_dir=output,
        language=language,
        model=model,
        preset=preset,
        formats=formats,
        device=device,
        compute_type=compute_type,
        beam_size=beam_size,
        vad_filter=not no_vad,
        initial_prompt=initial_prompt,
        cache_root=cache_root,
    )

    def progress(msg: str) -> None:
        console.print(msg)

    try:
        result = run_transcribe(request, progress=progress)
    except SermonScriptError as exc:
        console.print(f"[red]오류:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print()
    console.print("[bold green]변환 결과 요약[/bold green]")
    console.print(f"- job_id: {result.job_id}")
    console.print(f"- processed.wav: {result.processed_audio}")
    console.print(f"- 소요 시간: {result.elapsed_seconds:.2f}초")
    console.print("- 생성된 파일:")
    for path in result.exports:
        console.print(f"  • {path}")


if __name__ == "__main__":
    app()
