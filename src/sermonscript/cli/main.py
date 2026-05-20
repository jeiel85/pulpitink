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
from sermonscript.core.export.pipeline import ExportPipeline
from sermonscript.core.reference.corrections import apply_correction_to_segment
from sermonscript.core.transcription.base import (
    TranscriptionResult,
    TranscriptSegment,
)
from sermonscript.services.diagnostics import DoctorReport, run_doctor
from sermonscript.services.model_service import list_models, model_cache_dir
from sermonscript.services.settings_service import SettingsService
from sermonscript.services.transcribe_service import (
    TranscribeRequest,
    run_transcribe,
)
from sermonscript.storage.database import connect, default_db_path, initialise_database
from sermonscript.storage.job_repository import JobRepository

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
    reference: Path | None = typer.Option(
        None,
        "--reference",
        help="설교 원문 TXT/Markdown. 핵심 용어를 추출해 initial_prompt 와 교정 후보를 생성합니다.",
    ),
    user_dict: Path | None = typer.Option(
        None,
        "--user-dict",
        help="사용자 사전 JSON 파일. 기본 사전 위에 누적 적용됩니다.",
    ),
    cache_root: Path = typer.Option(
        Path("cache") / "jobs",
        "--cache-root",
        help="전처리 결과(processed.wav)를 저장할 cache/jobs 경로",
    ),
    fuzzy: bool = typer.Option(
        None,
        "--fuzzy/--no-fuzzy",
        help="자모 Fuzzy 매칭 활성화 여부 (지정하지 않으면 사용자 설정 사용)",
    ),
    fuzzy_threshold: float = typer.Option(
        None,
        "--fuzzy-threshold",
        help="자모 Fuzzy 매칭 임계값 (0.6 ~ 0.9) (지정하지 않으면 사용자 설정 사용)",
    ),
) -> None:
    """로컬 오디오 파일을 전처리 → STT → Export 파이프라인으로 변환합니다."""

    formats = _parse_formats(fmt)
    settings = SettingsService().load()

    actual_fuzzy = fuzzy if fuzzy is not None else settings.fuzzy_matching_enabled
    actual_threshold = fuzzy_threshold if fuzzy_threshold is not None else settings.fuzzy_threshold

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
        reference_path=reference,
        user_dict_path=user_dict,
        fuzzy_matching_enabled=actual_fuzzy,
        fuzzy_threshold=actual_threshold,
    )

    def progress(msg: str) -> None:
        console.print(msg)

    try:
        result = run_transcribe(request, progress=progress, persist=True)
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
    if result.reference is not None:
        console.print(f"- 원문: {result.reference.source_path}")
        console.print(f"- 교정 후보(pending): {result.correction_count}개")


jobs_app = typer.Typer(help="저장된 작업(jobs) 관리", no_args_is_help=True)
settings_app = typer.Typer(help="사용자 설정 관리", no_args_is_help=True)
models_app = typer.Typer(help="STT 모델 정보 조회", no_args_is_help=True)
corrections_app = typer.Typer(help="원문 대조 교정 후보 검토", no_args_is_help=True)

app.add_typer(jobs_app, name="jobs")
app.add_typer(settings_app, name="settings")
app.add_typer(models_app, name="models")
app.add_typer(corrections_app, name="corrections")


def _open_repo() -> tuple[object, JobRepository]:
    initialise_database()
    conn = connect()
    return conn, JobRepository(conn)


@jobs_app.command("list")
def jobs_list(limit: int = typer.Option(20, "--limit", "-n", help="표시할 작업 개수")) -> None:
    """최근 작업을 표 형태로 표시합니다."""

    conn, repo = _open_repo()
    try:
        rows = repo.list_jobs(limit=limit)
    finally:
        conn.close()

    if not rows:
        console.print("[yellow]저장된 작업이 없습니다.[/yellow]")
        return

    table = Table(title="최근 작업")
    table.add_column("id", style="bold")
    table.add_column("title")
    table.add_column("status")
    table.add_column("model")
    table.add_column("preset")
    table.add_column("created_at")
    for row in rows:
        status_style = {
            "completed": "[green]completed[/green]",
            "running": "[cyan]running[/cyan]",
            "failed": "[red]failed[/red]",
        }.get(row.status, row.status)
        table.add_row(
            row.id,
            row.title,
            status_style,
            row.model_name,
            row.preset,
            row.created_at,
        )
    console.print(table)


@jobs_app.command("show")
def jobs_show(job_id: str = typer.Argument(..., help="작업 ID")) -> None:
    """작업의 메타데이터, 세그먼트 수, export 목록을 표시합니다."""

    conn, repo = _open_repo()
    try:
        job = repo.get_job(job_id)
        if job is None:
            console.print(f"[red]작업을 찾을 수 없습니다: {job_id}[/red]")
            raise typer.Exit(code=1)
        segments = repo.list_segments(job_id)
        exports = repo.list_exports(job_id)
    finally:
        conn.close()

    console.print(f"[bold]작업 {job.id}[/bold]")
    console.print(f"- title: {job.title}")
    console.print(f"- source: {job.source_path}")
    console.print(f"- status: {job.status}")
    console.print(f"- model: {job.model_name} ({job.engine})")
    console.print(f"- preset: {job.preset}")
    console.print(f"- language: {job.language or 'auto'}")
    if job.duration_sec is not None:
        console.print(f"- duration: {job.duration_sec:.2f}s")
    if job.error_message:
        console.print(f"- error: [red]{job.error_message}[/red]")
    console.print(f"- created_at: {job.created_at}")
    console.print(f"- updated_at: {job.updated_at}")
    console.print(f"- segments: {len(segments)}")
    if exports:
        console.print("- exports:")
        for exp in exports:
            console.print(f"  • [{exp.format}] {exp.output_path}")


@jobs_app.command("export")
def jobs_export(
    job_id: str = typer.Argument(..., help="작업 ID"),
    output: Path = typer.Option(
        Path("./exports"), "--output", "-o", help="export 결과를 저장할 디렉터리"
    ),
    fmt: str = typer.Option(
        "txt,json,md,srt,vtt", "--format", "-f", help="콤마로 구분된 포맷 목록"
    ),
) -> None:
    """저장된 작업을 다시 export 합니다 (원본 오디오 재처리 없이 세그먼트 사용)."""

    formats = _parse_formats(fmt)
    conn, repo = _open_repo()
    try:
        job = repo.get_job(job_id)
        if job is None:
            console.print(f"[red]작업을 찾을 수 없습니다: {job_id}[/red]")
            raise typer.Exit(code=1)
        seg_rows = repo.list_segments(job_id)
    finally:
        conn.close()

    if not seg_rows:
        console.print("[yellow]세그먼트가 없어 export 할 내용이 없습니다.[/yellow]")
        raise typer.Exit(code=1)

    segments = [
        TranscriptSegment(
            start=s.start_sec,
            end=s.end_sec,
            text=s.raw_text,
            avg_logprob=s.avg_logprob,
            no_speech_prob=s.no_speech_prob,
            speaker=s.speaker,
            clean_text=s.clean_text,
            edited_text=s.edited_text,
        )
        for s in seg_rows
    ]
    source = Path(job.source_path)
    result = TranscriptionResult(
        source_path=source,
        audio_path=source,
        language=job.language,
        model_name=job.model_name,
        preset=job.preset,
        segments=segments,
        duration=job.duration_sec,
    )
    pipeline = ExportPipeline(formats)
    base_name = source.stem or job.title or job.id
    paths = pipeline.run(result, output, base_name)
    console.print(f"[green]생성된 파일 {len(paths)}개[/green]")
    for path in paths:
        console.print(f"  • {path}")


@settings_app.command("show")
def settings_show() -> None:
    """현재 저장된 사용자 설정을 표시합니다."""

    svc = SettingsService()
    current = svc.load()
    table = Table(title="SermonScript 설정")
    table.add_column("키", style="bold")
    table.add_column("값")
    for key in SettingsService.known_keys():
        value = getattr(current, key)
        if key == "output_dir" and not value:
            value = f"(기본값: {current.resolved_output_dir()})"
        elif key == "model_cache_dir" and not value:
            value = f"(기본값: {current.resolved_model_cache_dir()})"
        table.add_row(key, str(value))
    console.print(table)
    console.print(f"[dim]설정 파일: {svc.path}[/dim]")


@settings_app.command("set")
def settings_set(
    key: str = typer.Argument(..., help=f"설정 키: {', '.join(SettingsService.known_keys())}"),
    value: str = typer.Argument(..., help="새 값"),
) -> None:
    """단일 설정 값을 갱신합니다."""

    svc = SettingsService()
    try:
        updated = svc.update(**{key: value})
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]설정 갱신:[/green] {key} = {getattr(updated, key)!r}")


@models_app.command("list")
def models_list() -> None:
    """faster-whisper에서 사용할 수 있는 모델 목록을 표시합니다."""

    table = Table(title="지원 모델")
    table.add_column("이름", style="bold")
    table.add_column("크기")
    table.add_column("권장 compute_type")
    table.add_column("설명")
    for model in list_models():
        table.add_row(
            model.name,
            model.size_label,
            model.recommended_compute_type,
            model.description,
        )
    console.print(table)


@models_app.command("cache-dir")
def models_cache_dir() -> None:
    """현재 사용 중인 모델 캐시 경로를 표시합니다."""

    settings = SettingsService().load()
    cache = model_cache_dir(settings.model_cache_dir or None)
    console.print(str(cache))


@corrections_app.command("list")
def corrections_list(
    job_id: str = typer.Argument(..., help="작업 ID"),
    status: str = typer.Option(
        "pending", "--status", help="필터링할 상태 (pending/applied/ignored/all)"
    ),
) -> None:
    """작업의 교정 후보를 표시합니다."""

    status_filter = None if status == "all" else status
    conn, repo = _open_repo()
    try:
        rows = repo.list_correction_suggestions(job_id, status=status_filter)
    finally:
        conn.close()

    if not rows:
        console.print("[yellow]표시할 교정 후보가 없습니다.[/yellow]")
        return

    table = Table(title=f"교정 후보 ({status})")
    table.add_column("id", style="bold")
    table.add_column("segment")
    table.add_column("kind")
    table.add_column("원본")
    table.add_column("→ 제안")
    table.add_column("status")
    for row in rows:
        table.add_row(
            str(row.id),
            str(row.segment_id),
            row.kind,
            row.original_text,
            row.suggested_text,
            row.status,
        )
    console.print(table)


@corrections_app.command("apply")
def corrections_apply(
    suggestion_id: int = typer.Argument(..., help="적용할 교정 후보 ID"),
) -> None:
    """교정 후보를 적용해 해당 세그먼트의 edited_text를 갱신합니다."""

    conn, repo = _open_repo()
    try:
        candidates = [
            s
            for s in repo.list_correction_suggestions(_resolve_job_for_suggestion(repo, suggestion_id))
            if s.id == suggestion_id
        ]
        if not candidates:
            console.print(f"[red]교정 후보를 찾을 수 없습니다: {suggestion_id}[/red]")
            raise typer.Exit(code=1)
        suggestion = candidates[0]
        if suggestion.status == "applied":
            console.print("[yellow]이미 적용된 후보입니다.[/yellow]")
            return
        segment = repo.get_segment(suggestion.segment_id)
        if segment is None:
            console.print(f"[red]세그먼트를 찾을 수 없습니다: {suggestion.segment_id}[/red]")
            raise typer.Exit(code=1)
        new_edited = apply_correction_to_segment(
            raw_text=segment.raw_text,
            clean_text=segment.clean_text,
            edited_text=segment.edited_text,
            original=suggestion.original_text,
            suggested=suggestion.suggested_text,
        )
        repo.update_segment_text(segment.id, edited_text=new_edited)
        repo.update_correction_status(suggestion_id, status="applied")
        console.print(f"[green]적용:[/green] segment={segment.id} → {new_edited}")
    finally:
        conn.close()


@corrections_app.command("ignore")
def corrections_ignore(
    suggestion_id: int = typer.Argument(..., help="무시할 교정 후보 ID"),
) -> None:
    """교정 후보를 무시 상태로 표시합니다."""

    conn, repo = _open_repo()
    try:
        repo.update_correction_status(suggestion_id, status="ignored")
    finally:
        conn.close()
    console.print(f"[yellow]무시:[/yellow] suggestion={suggestion_id}")


def _resolve_job_for_suggestion(repo: JobRepository, suggestion_id: int) -> str:
    row = repo._conn.execute(  # noqa: SLF001 - intentional internal access
        "SELECT job_id FROM correction_suggestions WHERE id = ?", (suggestion_id,)
    ).fetchone()
    if row is None:
        raise typer.BadParameter(f"교정 후보를 찾을 수 없습니다: {suggestion_id}")
    return row["job_id"]


@app.command("db-path")
def db_path() -> None:
    """SermonScript SQLite DB 파일 경로를 표시합니다."""

    console.print(str(default_db_path()))


if __name__ == "__main__":
    app()
