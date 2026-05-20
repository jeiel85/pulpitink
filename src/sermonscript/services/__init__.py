"""Higher-level services orchestrating ``core`` modules.

These services are pure Python and can be reused by the CLI and the GUI.
"""

from sermonscript.services.diagnostics import (
    DoctorReport,
    DoctorResult,
    run_doctor,
)
from sermonscript.services.model_service import (
    SUPPORTED_MODELS,
    ModelInfo,
    is_supported,
    list_models,
    model_cache_dir,
)
from sermonscript.services.settings_service import (
    SETTINGS_FILENAME,
    Settings,
    SettingsService,
    settings_path,
)
from sermonscript.services.transcribe_service import (
    SUPPORTED_INPUT_EXTENSIONS,
    TranscribeRequest,
    TranscribeResult,
    new_job_id,
    run_transcribe,
    validate_input_path,
)

__all__ = [
    "DoctorReport",
    "DoctorResult",
    "ModelInfo",
    "SETTINGS_FILENAME",
    "SUPPORTED_INPUT_EXTENSIONS",
    "SUPPORTED_MODELS",
    "Settings",
    "SettingsService",
    "TranscribeRequest",
    "TranscribeResult",
    "is_supported",
    "list_models",
    "model_cache_dir",
    "new_job_id",
    "run_doctor",
    "run_transcribe",
    "settings_path",
    "validate_input_path",
]
