"""Higher-level services orchestrating ``core`` modules.

These services are pure Python and can be reused by the CLI and (later) GUI.
"""

from sermonscript.services.diagnostics import (
    DoctorReport,
    DoctorResult,
    run_doctor,
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
    "SUPPORTED_INPUT_EXTENSIONS",
    "TranscribeRequest",
    "TranscribeResult",
    "new_job_id",
    "run_doctor",
    "run_transcribe",
    "validate_input_path",
]
