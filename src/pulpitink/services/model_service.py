"""Supported STT model catalog and cache helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pulpitink.app.paths import get_app_paths


@dataclass(frozen=True)
class ModelInfo:
    """Static metadata about a supported faster-whisper model."""

    name: str
    description: str
    size_label: str
    recommended_compute_type: str = "int8"


SUPPORTED_MODELS: tuple[ModelInfo, ...] = (
    ModelInfo("tiny", "가장 빠르지만 정확도 낮음. 빠른 미리보기용.", "≈ 75 MB"),
    ModelInfo("base", "tiny와 small 사이의 절충안.", "≈ 142 MB"),
    ModelInfo("small", "기본 권장 모델. 한국어 설교에 적합.", "≈ 466 MB"),
    ModelInfo(
        "medium",
        "small 대비 더 정확하나 메모리 사용량 증가.",
        "≈ 1.5 GB",
    ),
    ModelInfo(
        "large-v3",
        "최고 정확도. GPU 사용 권장.",
        "≈ 3 GB",
        recommended_compute_type="float16",
    ),
)

_MODEL_NAMES = frozenset(m.name for m in SUPPORTED_MODELS)


def list_models() -> tuple[ModelInfo, ...]:
    """Return the supported model catalogue."""

    return SUPPORTED_MODELS


def is_supported(name: str) -> bool:
    return name in _MODEL_NAMES


def model_cache_dir(override: str | Path | None = None) -> Path:
    """Return the directory used for cached model weights."""

    if override:
        path = Path(override)
    else:
        path = get_app_paths().ensure().models_dir
    path.mkdir(parents=True, exist_ok=True)
    return path
