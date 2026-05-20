"""User preferences persisted as JSON next to the SQLite DB.

Kept deliberately small in Goal 2 — only the fields the CLI / GUI need
right now. Future fields should be added with a default so older config
files continue to load.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from pulpitink.app.paths import get_app_paths
from pulpitink.core.audio.ffmpeg_runner import DEFAULT_PRESET

logger = logging.getLogger("pulpitink.settings")

SETTINGS_FILENAME = "settings.json"


@dataclass(frozen=True)
class Settings:
    """User preferences exposed by ``settings show/set``."""

    language: str = "ko"
    model: str = "small"
    preset: str = DEFAULT_PRESET
    output_dir: str = ""  # empty -> resolved to <data_dir>/exports
    model_cache_dir: str = ""  # empty -> resolved to <data_dir>/models
    fuzzy_matching_enabled: bool = True
    fuzzy_threshold: float = 0.70
    keep_history: bool = True

    def resolved_output_dir(self) -> Path:
        if self.output_dir:
            return Path(self.output_dir)
        return get_app_paths().data_dir / "exports"

    def resolved_model_cache_dir(self) -> Path:
        if self.model_cache_dir:
            return Path(self.model_cache_dir)
        return get_app_paths().models_dir


_KNOWN_FIELDS = {f.name for f in fields(Settings)}


def settings_path() -> Path:
    return get_app_paths().ensure().data_dir / SETTINGS_FILENAME


class SettingsService:
    """Load / save / mutate user preferences."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path is not None else settings_path()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Settings:
        if not self._path.exists():
            return Settings()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("settings.json 읽기 실패, 기본값 사용: %s", exc)
            return Settings()

        clean = {k: v for k, v in raw.items() if k in _KNOWN_FIELDS}
        return Settings(**clean)

    def save(self, settings: Settings) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update(self, **kwargs: object) -> Settings:
        unknown = sorted(set(kwargs) - _KNOWN_FIELDS)
        if unknown:
            raise KeyError(
                f"알 수 없는 설정 키: {', '.join(unknown)}. "
                f"사용 가능: {', '.join(sorted(_KNOWN_FIELDS))}"
            )

        # Enforce proper types for values that may come in as strings from CLI
        converted: dict[str, object] = {}
        for k, v in kwargs.items():
            if k in ("fuzzy_matching_enabled", "keep_history"):
                if isinstance(v, str):
                    converted[k] = v.lower() in ("true", "1", "yes", "on")
                else:
                    converted[k] = bool(v)
            elif k == "fuzzy_threshold":
                try:
                    converted[k] = float(v)  # type: ignore
                except (ValueError, TypeError):
                    raise ValueError(f"'{v}'는 유효한 float 임계값이 아닙니다.") from None
            else:
                converted[k] = v

        merged = replace(self.load(), **converted)  # type: ignore[arg-type]
        self.save(merged)
        return merged

    @staticmethod
    def known_keys() -> tuple[str, ...]:
        return tuple(sorted(_KNOWN_FIELDS))
