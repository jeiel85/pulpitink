# PyInstaller spec for PulpitInk CLI Sidecar (Tauri Integration).
#
# This build is optimized as a background console executable to serve as a 
# Tauri Sidecar. It does not include the PySide6 UI modules, reducing size.

# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(os.environ.get("PULPIT_INK_ROOT", os.getcwd())).resolve()
ENTRY = str(PROJECT_ROOT / "src" / "pulpit_ink" / "cli" / "main.py")

# Keep ``src`` on sys.path so the analysis pass resolves
# ``pulpit_ink.*`` modules without an installed wheel.
SRC_DIR = str(PROJECT_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

hidden_imports = [
    # Core Audio & Transcription
    "pulpit_ink.core.audio.enhancement_presets",
    "pulpit_ink.core.audio.ffmpeg_runner",
    "pulpit_ink.core.transcription.base",
    "pulpit_ink.core.transcription.faster_whisper_engine",
    
    # Exporters
    "pulpit_ink.core.export.base",
    "pulpit_ink.core.export.json_exporter",
    "pulpit_ink.core.export.markdown_exporter",
    "pulpit_ink.core.export.srt_exporter",
    "pulpit_ink.core.export.txt_exporter",
    "pulpit_ink.core.export.vtt_exporter",
    "pulpit_ink.core.export.pipeline",
    
    # Postprocessors & Jamo
    "pulpit_ink.core.postprocess.jamo",
    "pulpit_ink.core.postprocess.bible_refs",
    "pulpit_ink.core.postprocess.lexicon",
    "pulpit_ink.core.postprocess.pipeline",
    
    # Alignment & Reference
    "pulpit_ink.core.reference.aligner",
    "pulpit_ink.core.reference.corrections",
    "pulpit_ink.core.reference.parser",
    "pulpit_ink.core.reference.prompt_builder",
    
    # Services
    "pulpit_ink.services.diagnostics",
    "pulpit_ink.services.model_service",
    "pulpit_ink.services.settings_service",
    "pulpit_ink.services.transcribe_service",
    
    # Storage
    "pulpit_ink.storage.database",
    "pulpit_ink.storage.job_repository",
    
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
    name="pulpit-ink-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Console enabled for capturing stdout/stderr streams
    icon=str(PROJECT_ROOT / "src" / "pulpit_ink" / "resources" / "pulpit-ink.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="pulpit-ink-sidecar",
)
