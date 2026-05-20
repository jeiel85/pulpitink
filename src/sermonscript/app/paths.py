"""Application data paths.

Uses ``platformdirs`` so we follow the platform-appropriate locations
(Windows ``%LOCALAPPDATA%``, macOS ``~/Library/Application Support``, Linux XDG).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_cache_dir, user_data_dir, user_log_dir

_APP_NAME = "SermonScript"
_APP_AUTHOR = "SermonScript"


@dataclass(frozen=True)
class AppPaths:
    """Resolved application paths."""

    data_dir: Path
    cache_dir: Path
    log_dir: Path
    models_dir: Path
    jobs_dir: Path

    def ensure(self) -> AppPaths:
        for path in (self.data_dir, self.cache_dir, self.log_dir, self.models_dir, self.jobs_dir):
            path.mkdir(parents=True, exist_ok=True)
        return self


def get_app_paths() -> AppPaths:
    """Return the canonical SermonScript application paths."""

    data_dir = Path(user_data_dir(_APP_NAME, _APP_AUTHOR))
    cache_dir = Path(user_cache_dir(_APP_NAME, _APP_AUTHOR))
    log_dir = Path(user_log_dir(_APP_NAME, _APP_AUTHOR))
    return AppPaths(
        data_dir=data_dir,
        cache_dir=cache_dir,
        log_dir=log_dir,
        models_dir=data_dir / "models",
        jobs_dir=cache_dir / "jobs",
    )


def job_cache_dir(job_id: str, *, base: Path | None = None) -> Path:
    """Return ``cache/jobs/<job_id>`` next to the working directory when ``base`` is unset."""

    root = base if base is not None else Path("cache") / "jobs"
    target = root / job_id
    target.mkdir(parents=True, exist_ok=True)
    return target
