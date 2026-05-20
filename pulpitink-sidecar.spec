# PyInstaller spec for PulpitInk CLI Sidecar (Tauri Integration).
#
# This build is optimized as a background console executable to serve as a 
# Tauri Sidecar. It does not include the PySide6 UI modules, reducing size.

# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(os.environ.get("PULPITINK_ROOT", os.getcwd())).resolve()
ENTRY = str(PROJECT_ROOT / "src" / "pulpitink" / "cli" / "main.py")

# Keep ``src`` on sys.path so the analysis pass resolves
# ``pulpitink.*`` modules without an installed wheel.
SRC_DIR = str(PROJECT_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

hidden_imports = [
    # Core Audio & Transcription
    "pulpitink.core.audio.enhancement_presets",
    "pulpitink.core.audio.ffmpeg_runner",
    "pulpitink.core.transcription.base",
    "pulpitink.core.transcription.faster_whisper_engine",
    
    # Exporters
    "pulpitink.core.export.base",
    "pulpitink.core.export.json_exporter",
    "pulpitink.core.export.markdown_exporter",
    "pulpitink.core.export.srt_exporter",
    "pulpitink.core.export.txt_exporter",
    "pulpitink.core.export.vtt_exporter",
    "pulpitink.core.export.pipeline",
    
    # Postprocessors & Jamo
    "pulpitink.core.postprocess.jamo",
    "pulpitink.core.postprocess.bible_refs",
    "pulpitink.core.postprocess.lexicon",
    "pulpitink.core.postprocess.pipeline",
    
    # Alignment & Reference
    "pulpitink.core.reference.aligner",
    "pulpitink.core.reference.corrections",
    "pulpitink.core.reference.parser",
    "pulpitink.core.reference.prompt_builder",
    
    # Services
    "pulpitink.services.diagnostics",
    "pulpitink.services.model_service",
    "pulpitink.services.settings_service",
    "pulpitink.services.transcribe_service",
    
    # Storage
    "pulpitink.storage.database",
    "pulpitink.storage.job_repository",
    
    # RapidFuzz and external deps
    "rapidfuzz",
    "typer",
    "rich",
    "pydantic",
    "platformdirs",
]

excludes = [
    # Exclude PySide6 GUI to save space
    "PySide6",
    "PyQt5",
    "PyQt6",
    
    # Heavy scientific / testing suites
    "torch.distributions",
    "torch.testing",
    "tensorflow",
    "matplotlib.tests",
]

a = Analysis(
    [ENTRY],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pulpitink-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Console enabled for capturing stdout/stderr streams
    icon=str(PROJECT_ROOT / "src" / "pulpitink" / "resources" / "pulpitink.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="pulpitink-sidecar",
)
