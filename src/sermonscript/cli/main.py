import platform
import shutil
import sys
from pathlib import Path

import typer
from platformdirs import user_data_dir
from rich.console import Console

from sermonscript import __version__

app = typer.Typer(help="SermonScript CLI")
console = Console()


@app.command()
def doctor() -> None:
    """Check local development/runtime environment."""
    console.print(f"SermonScript: {__version__}")
    console.print(f"Python: {sys.version.split()[0]}")
    console.print(f"OS: {platform.platform()}")

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        console.print(f"FFmpeg: found at {ffmpeg_path}")
    else:
        console.print("FFmpeg: not found")

    data_dir = Path(user_data_dir("SermonScript", "SermonScript"))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        console.print(f"Data dir: writable ({data_dir})")
    except OSError as exc:
        console.print(f"Data dir: not writable ({data_dir}) - {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def transcribe(
    input_path: Path = typer.Argument(..., help="Local audio/video file path"),
    language: str = typer.Option("ko", help="Language code"),
    model: str = typer.Option("small", help="Whisper model name"),
    preset: str = typer.Option("sermon", help="Audio preprocessing preset"),
    output: Path = typer.Option(Path("./exports"), help="Output directory"),
) -> None:
    """Placeholder for future transcription command."""
    if not input_path.exists():
        console.print(f"Input file not found: {input_path}")
        raise typer.Exit(code=1)

    console.print("Transcription is not implemented yet.")
    console.print(f"Input: {input_path}")
    console.print(f"Language: {language}")
    console.print(f"Model: {model}")
    console.print(f"Preset: {preset}")
    console.print(f"Output: {output}")
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
