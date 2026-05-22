"""PulpitInk CLI entry point.

Built on Typer. Keep the CLI thin — orchestrate ``pulpit_ink.services``
modules so the same code can be reused from the future PySide6 GUI.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pulpit_ink import __version__
from pulpit_ink.app.exceptions import PulpitInkError
from pulpit_ink.app.logging_config import configure_logging
from pulpit_ink.app.paths import get_app_paths
from pulpit_ink.core.audio.enhancement_presets import PRESETS
from pulpit_ink.core.audio.ffmpeg_runner import DEFAULT_PRESET
from pulpit_ink.core.audio.youtube_downloader import (
    install_yt_dlp,
    is_yt_dlp_available,
)
from pulpit_ink.core.export.base import ExportFormat
from pulpit_ink.core.export.pipeline import ExportPipeline
from pulpit_ink.core.postprocess.lexicon import save_user_lexicon
from pulpit_ink.core.reference.corrections import apply_correction_to_segment
from pulpit_ink.core.transcription.base import (
    TranscriptionResult,
    TranscriptSegment,
)
from pulpit_ink.core.utils.update_checker import check_for_updates
from pulpit_ink.services.diagnostics import DoctorReport, run_doctor
from pulpit_ink.services.model_service import list_models, model_cache_dir
from pulpit_ink.services.settings_service import SettingsService
from pulpit_ink.services.transcribe_service import (
    TranscribeRequest,
    run_transcribe,
)
from pulpit_ink.storage.database import connect, default_db_path, initialise_database
from pulpit_ink.storage.job_repository import JobRepository

app = typer.Typer(
    help="설교필기 (PulpitInk): 로컬 설교/강의 녹음 STT 도구",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _print_doctor_report(report: DoctorReport) -> None:
    table = Table(title="PulpitInk 환경 진단", show_lines=False)
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
    """현재 PulpitInk 버전을 출력합니다."""

    console.print(f"PulpitInk {__version__}")


@app.command()
def doctor() -> None:
    """현재 환경이 PulpitInk 실행에 적합한지 확인합니다."""

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
        "txt,json,md,srt,vtt,csv,docx",
        "--format",
        "-f",
        help="콤마로 구분된 출력 포맷 목록 (지원: txt, json, md, srt, vtt, csv, docx)",
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
    diarize: bool = typer.Option(
        False,
        "--diarize",
        help="Heuristic 화자 분리(Diarization) 활성화 여부",
    ),
) -> None:
    """로컬 오디오 파일을 전처리 → STT → Export 파이프라인으로 변환합니다."""

    formats = _parse_formats(fmt)
    settings = SettingsService().load()

    input_str = str(input_path)
    if input_str.startswith(("http://", "https://")):
        console.print(f"[bold blue]YouTube URL 감지:[/bold blue] {input_str}")
        console.print("오디오 다운로드를 진행합니다. (yt-dlp 구동)")
        from pulpit_ink.core.audio.youtube_downloader import download_youtube_audio
        try:
            downloaded_path = download_youtube_audio(input_str, output)
            console.print(f"[bold green]다운로드 완료:[/bold green] {downloaded_path.name}")
            input_path = downloaded_path
        except Exception as exc:
            console.print(f"[red]YouTube 다운로드 실패:[/red] {exc}")
            raise typer.Exit(code=1) from exc

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
        diarize=diarize,
    )

    def progress(msg: str) -> None:
        console.print(msg)

    try:
        result = run_transcribe(request, progress=progress, persist=True)
    except PulpitInkError as exc:
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
def jobs_list(
    limit: int = typer.Option(20, "--limit", "-n", help="표시할 작업 개수"),
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """최근 작업을 표 형태로 표시합니다."""

    conn, repo = _open_repo()
    try:
        rows = repo.list_jobs(limit=limit)
    finally:
        conn.close()

    if not rows:
        if json_output:
            print("[]")
            return
        console.print("[yellow]저장된 작업이 없습니다.[/yellow]")
        return

    if json_output:
        print(json.dumps([asdict(row) for row in rows], ensure_ascii=False))
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
def jobs_show(
    job_id: str = typer.Argument(..., help="작업 ID"),
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """작업의 메타데이터, 세그먼트 수, export 목록을 표시합니다."""

    conn, repo = _open_repo()
    try:
        job = repo.get_job(job_id)
        if job is None:
            console.print(f"[red]작업을 찾을 수 없습니다: {job_id}[/red]")
            raise typer.Exit(code=1)
        segments = repo.list_segments(job_id)
        exports = repo.list_exports(job_id)
        references = repo.list_reference_documents(job_id)
        corrections = repo.list_correction_suggestions(job_id)
    finally:
        conn.close()

    if json_output:
        payload = {
            "job": asdict(job),
            "segments": [asdict(segment) for segment in segments],
            "exports": [asdict(export) for export in exports],
            "reference": asdict(references[0]) if references else None,
            "references": [asdict(reference) for reference in references],
            "corrections": [asdict(correction) for correction in corrections],
        }
        print(json.dumps(payload, ensure_ascii=False))
        return

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
        "txt,json,md,srt,vtt,csv,docx",
        "--format",
        "-f",
        help="콤마로 구분된 포맷 목록 (지원: txt, json, md, srt, vtt, csv, docx)",
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

        # Load bible_refs from database reference documents
        bible_refs = []
        try:
            ref_docs = repo.list_reference_documents(job_id)
            for doc in ref_docs:
                if doc.bible_refs:
                    bible_refs.extend(doc.bible_refs)
        except Exception:
            pass
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
    paths = pipeline.run(result, output, base_name, bible_refs=bible_refs)
    console.print(f"[green]생성된 파일 {len(paths)}개[/green]")
    for path in paths:
        console.print(f"  • {path}")


@jobs_app.command("delete")
def jobs_delete(
    job_id: str = typer.Argument(..., help="삭제할 작업 ID"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="확인 메세지를 생략하고 즉시 삭제합니다."
    ),
    cache_root: Path = typer.Option(
        Path("cache") / "jobs",
        "--cache-root",
        help="전처리 결과(processed.wav)가 저장되어 있는 cache/jobs 경로",
    ),
) -> None:
    """특정 작업 데이터와 해당 캐시 파일을 완전히 삭제합니다."""
    conn, repo = _open_repo()
    try:
        job = repo.get_job(job_id)
        if job is None:
            console.print(f"[red]오류: ID가 '{job_id}'인 작업을 찾을 수 없습니다.[/red]")
            raise typer.Exit(code=1)

        if not yes:
            confirm = typer.confirm(
                f"정말로 작업 '{job.title}' ({job_id})의 모든 데이터와 캐시 오디오를 삭제하시겠습니까?"
            )
            if not confirm:
                console.print("삭제 작업을 취소했습니다.")
                return

        # 1. DB에서 작업 삭제 (cascade 제약에 의해 segments, exports 등도 삭제됨)
        repo.delete_job(job_id)
        console.print(f"[green]작업 '{job_id}'의 DB 레코드가 성공적으로 삭제되었습니다.[/green]")

        # 2. 캐시 디렉터리 삭제
        import shutil
        job_cache_dir = (cache_root / job_id).resolve()
        if job_cache_dir.exists() and job_cache_dir.is_dir():
            shutil.rmtree(job_cache_dir)
            console.print(f"[green]캐시 디렉터리 '{job_cache_dir}'가 성공적으로 삭제되었습니다.[/green]")
        else:
            console.print(f"[yellow]알림: 캐시 디렉터리 '{job_cache_dir}'가 존재하지 않아 삭제를 생략합니다.[/yellow]")

    finally:
        conn.close()  # type: ignore


@jobs_app.command("clean-cache")
def jobs_clean_cache(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="확인 메세지를 생략하고 즉시 삭제합니다."
    ),
    cache_root: Path = typer.Option(
        Path("cache") / "jobs",
        "--cache-root",
        help="전처리 결과(processed.wav)가 저장되어 있는 cache/jobs 경로",
    ),
) -> None:
    """DB에 등록되어 있지 않은 작업 캐시 디렉터리를 포함해 모든 캐시 디렉터리를 일괄 정리합니다."""
    # DB에 등록되어 있는 모든 job_id 목록 구하기
    conn, repo = _open_repo()
    try:
        jobs = repo.list_jobs(limit=10000)
        active_job_ids = {j.id for j in jobs}
    finally:
        conn.close()  # type: ignore

    if not cache_root.exists() or not cache_root.is_dir():
        console.print(f"[yellow]알림: 캐시 디렉터리 '{cache_root}'가 존재하지 않습니다.[/yellow]")
        return

    import shutil
    # cache_root의 자식 폴더들 중 DB에 없는 것만 탐색
    subdirs = [p for p in cache_root.iterdir() if p.is_dir() and p.name not in active_job_ids]
    if not subdirs:
        console.print("[green]정리할 미등록(고스트) 캐시 디렉터리가 없습니다.[/green]")
        return

    console.print(f"발견된 미등록 캐시 폴더 개수: {len(subdirs)}개")
    if not yes:
        confirm = typer.confirm("DB에 등록되지 않은 모든 작업 캐시 폴더를 정말로 삭제하시겠습니까?")
        if not confirm:
            console.print("캐시 정리를 취소했습니다.")
            return

    deleted_count = 0
    for subdir in subdirs:
        try:
            shutil.rmtree(subdir)
            deleted_count += 1
        except Exception as e:
            console.print(f"[red]오류: '{subdir.name}' 폴더 삭제 실패: {e}[/red]")

    console.print(f"[green]총 {deleted_count}개의 캐시 디렉터리를 성공적으로 정리했습니다.[/green]")


@settings_app.command("show")
def settings_show(
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """현재 저장된 사용자 설정을 표시합니다."""

    svc = SettingsService()
    current = svc.load()
    if json_output:
        print(json.dumps(asdict(current), ensure_ascii=False))
        return

    table = Table(title="PulpitInk 설정")
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
    """PulpitInk SQLite DB 파일 경로를 표시합니다."""

    console.print(str(default_db_path()))


# ---------- Tauri/Frontend IPC helpers ----------

user_dict_app = typer.Typer(help="사용자 사전(Glossary) 관리", no_args_is_help=True)
youtube_app = typer.Typer(help="YouTube 입력 보조 도구", no_args_is_help=True)
segments_app = typer.Typer(help="세그먼트 편집 영속화", no_args_is_help=True)

app.add_typer(user_dict_app, name="user-dict")
app.add_typer(youtube_app, name="youtube")
app.add_typer(segments_app, name="segments")


def _default_user_dict_path() -> Path:
    return get_app_paths().ensure().data_dir / "user_dict.json"


def _load_user_dict_entries(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"사용자 사전 JSON 파싱 실패: {exc}") from exc
    if not isinstance(raw, dict):
        raise typer.BadParameter("사용자 사전 JSON은 객체(dict)여야 합니다.")
    result: dict[str, list[str]] = {}
    for canonical, forms in raw.items():
        if not isinstance(canonical, str):
            continue
        if isinstance(forms, str):
            result[canonical] = [forms]
        elif isinstance(forms, list):
            result[canonical] = [str(f) for f in forms if isinstance(f, str)]
        else:
            result[canonical] = []
    return result


@user_dict_app.command("path")
def user_dict_path() -> None:
    """기본 사용자 사전 파일 경로를 출력합니다."""

    console.print(str(_default_user_dict_path()))


@user_dict_app.command("list")
def user_dict_list(
    path: Path | None = typer.Option(
        None, "--path", help="사용자 사전 JSON 경로 (기본: %LOCALAPPDATA%/PulpitInk/user_dict.json)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """사용자 사전 항목 목록을 출력합니다."""

    target = path or _default_user_dict_path()
    entries = _load_user_dict_entries(target)

    if json_output:
        print(json.dumps({"path": str(target), "entries": entries}, ensure_ascii=False))
        return

    if not entries:
        console.print(f"[yellow]사용자 사전이 비어 있습니다.[/yellow] (경로: {target})")
        return

    table = Table(title=f"사용자 사전 ({len(entries)}개)")
    table.add_column("표준 단어", style="bold")
    table.add_column("STT 오인식 후보")
    for canonical, forms in sorted(entries.items()):
        table.add_row(canonical, ", ".join(forms) if forms else "—")
    console.print(table)


@user_dict_app.command("add")
def user_dict_add(
    canonical: str = typer.Argument(..., help="표준(정답) 단어"),
    wrong_forms: list[str] = typer.Argument(  # noqa: B008
        None, help="STT가 잘못 인식하는 후보 (공백으로 여러 개 지정)"
    ),
    path: Path | None = typer.Option(None, "--path", help="사용자 사전 JSON 경로"),
    json_output: bool = typer.Option(False, "--json", help="JSON으로 결과를 출력합니다."),
) -> None:
    """사용자 사전에 새 항목을 추가하거나 기존 항목을 갱신합니다."""

    target = path or _default_user_dict_path()
    entries = _load_user_dict_entries(target)
    existing = list(entries.get(canonical, []))
    for form in wrong_forms or []:
        if form and form != canonical and form not in existing:
            existing.append(form)
    entries[canonical] = existing
    save_user_lexicon(target, entries)

    if json_output:
        print(json.dumps({"ok": True, "path": str(target), "canonical": canonical, "wrong_forms": existing}, ensure_ascii=False))
        return
    console.print(f"[green]추가:[/green] {canonical} → {existing}")


@user_dict_app.command("remove")
def user_dict_remove(
    canonical: str = typer.Argument(..., help="삭제할 표준 단어"),
    path: Path | None = typer.Option(None, "--path", help="사용자 사전 JSON 경로"),
    json_output: bool = typer.Option(False, "--json", help="JSON으로 결과를 출력합니다."),
) -> None:
    """사용자 사전에서 항목을 제거합니다."""

    target = path or _default_user_dict_path()
    entries = _load_user_dict_entries(target)
    removed = entries.pop(canonical, None)
    save_user_lexicon(target, entries)

    if json_output:
        print(json.dumps({"ok": removed is not None, "path": str(target), "canonical": canonical}, ensure_ascii=False))
        return
    if removed is None:
        console.print(f"[yellow]해당 항목이 없습니다:[/yellow] {canonical}")
    else:
        console.print(f"[green]삭제:[/green] {canonical}")


@user_dict_app.command("import")
def user_dict_import(
    csv_path: Path = typer.Argument(..., help="가져올 CSV 파일 경로"),
    path: Path | None = typer.Option(None, "--path", help="대상 사용자 사전 JSON 경로"),
    merge: bool = typer.Option(
        True, "--merge/--replace", help="기본은 병합(merge), --replace 시 기존 항목 모두 대체"
    ),
    json_output: bool = typer.Option(False, "--json", help="JSON 결과를 출력합니다."),
) -> None:
    """CSV(첫 열: 표준, 이후 열: 오인식 후보)에서 사용자 사전을 가져옵니다."""

    import csv

    target = path or _default_user_dict_path()
    existing = _load_user_dict_entries(target) if merge else {}

    if not csv_path.exists():
        raise typer.BadParameter(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    added = 0
    with csv_path.open(encoding="utf-8") as fp:
        reader = csv.reader(fp)
        for row in reader:
            if not row:
                continue
            canonical = row[0].strip()
            if not canonical:
                continue
            forms = [cell.strip() for cell in row[1:] if cell.strip()]
            existing[canonical] = forms
            added += 1

    save_user_lexicon(target, existing)
    if json_output:
        print(json.dumps({"ok": True, "path": str(target), "imported": added, "total": len(existing)}, ensure_ascii=False))
        return
    console.print(f"[green]가져오기 완료:[/green] {added}개 항목 (총 {len(existing)}개)")


@user_dict_app.command("export")
def user_dict_export(
    csv_path: Path = typer.Argument(..., help="내보낼 CSV 파일 경로"),
    path: Path | None = typer.Option(None, "--path", help="대상 사용자 사전 JSON 경로"),
    json_output: bool = typer.Option(False, "--json", help="JSON 결과를 출력합니다."),
) -> None:
    """사용자 사전을 CSV로 내보냅니다."""

    import csv

    target = path or _default_user_dict_path()
    entries = _load_user_dict_entries(target)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        for canonical, forms in sorted(entries.items()):
            writer.writerow([canonical, *forms])

    if json_output:
        print(json.dumps({"ok": True, "path": str(csv_path), "exported": len(entries)}, ensure_ascii=False))
        return
    console.print(f"[green]내보내기 완료:[/green] {len(entries)}개 항목 → {csv_path}")


@app.command("update-check")
def update_check(
    force: bool = typer.Option(False, "--force", "-f", help="24시간 캐시를 무시하고 강제로 조회합니다."),
    current: str = typer.Option(__version__, "--current", help="비교 기준 버전 (기본: 현재 버전)"),
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """GitHub Releases에서 최신 버전을 조회하고 결과를 출력합니다."""

    has_update, latest, url, err = check_for_updates(current, force=force)
    payload = {
        "has_update": has_update,
        "current_version": current,
        "latest_version": latest,
        "download_url": url,
        "error": err,
    }
    if json_output:
        print(json.dumps(payload, ensure_ascii=False))
        return
    if err:
        console.print(f"[yellow]업데이트 확인 실패:[/yellow] {err}")
        return
    if has_update:
        console.print(f"[green]신규 버전:[/green] {latest} (현재 {current}) → {url}")
    else:
        console.print(f"[dim]최신 버전입니다.[/dim] (현재 {current})")


@youtube_app.command("check")
def youtube_check(
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """yt-dlp 라이브러리 설치 여부를 진단합니다."""

    available = is_yt_dlp_available()
    if json_output:
        print(json.dumps({"available": available}, ensure_ascii=False))
        return
    if available:
        console.print("[green]yt-dlp 설치됨[/green]")
    else:
        console.print("[yellow]yt-dlp 미설치 — `pulpit-ink youtube install` 명령으로 설치할 수 있습니다.[/yellow]")


@youtube_app.command("install")
def youtube_install(
    json_output: bool = typer.Option(False, "--json", help="Tauri/자동화용 JSON으로 출력합니다."),
) -> None:
    """현재 Python 환경에 yt-dlp를 pip로 설치합니다 (사용자 동의 후 호출)."""

    if is_yt_dlp_available():
        if json_output:
            print(json.dumps({"ok": True, "already": True}, ensure_ascii=False))
            return
        console.print("[dim]yt-dlp가 이미 설치되어 있습니다.[/dim]")
        return

    ok = install_yt_dlp()
    if json_output:
        print(json.dumps({"ok": ok, "already": False}, ensure_ascii=False))
        return
    if ok:
        console.print("[green]yt-dlp 설치 완료.[/green]")
    else:
        console.print("[red]yt-dlp 설치 실패. 수동으로 `pip install yt-dlp`를 시도하세요.[/red]")
        raise typer.Exit(code=1)


@segments_app.command("update")
def segments_update(
    segment_id: int = typer.Argument(..., help="segments.id"),
    edited_text: str | None = typer.Option(None, "--edited-text", help="edited_text 값"),
    clean_text: str | None = typer.Option(None, "--clean-text", help="clean_text 값"),
    speaker: str | None = typer.Option(None, "--speaker", help="화자 식별자"),
    json_output: bool = typer.Option(False, "--json", help="JSON 결과를 출력합니다."),
) -> None:
    """단일 세그먼트의 편집 필드를 갱신합니다 (raw_text는 변경 불가)."""

    if edited_text is None and clean_text is None and speaker is None:
        raise typer.BadParameter("적어도 하나의 필드(--edited-text/--clean-text/--speaker)를 지정하세요.")

    conn, repo = _open_repo()
    try:
        segment = repo.get_segment(segment_id)
        if segment is None:
            if json_output:
                print(json.dumps({"ok": False, "error": "segment not found"}, ensure_ascii=False))
                return
            console.print(f"[red]세그먼트를 찾을 수 없습니다: {segment_id}[/red]")
            raise typer.Exit(code=1)
        repo.update_segment_text(
            segment_id,
            edited_text=edited_text,
            clean_text=clean_text,
            speaker=speaker,
        )
    finally:
        conn.close()  # type: ignore

    if json_output:
        print(json.dumps({"ok": True, "segment_id": segment_id}, ensure_ascii=False))
        return
    console.print(f"[green]갱신:[/green] segment={segment_id}")


if __name__ == "__main__":
    app()
