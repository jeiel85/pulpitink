# PyInstaller spec for PulpitInk (설교필기) — Windows portable build.
#
# IMPORTANT: this spec deliberately does NOT bundle:
#   - FFmpeg binaries (license + size + per-user system FFmpeg)
#   - faster-whisper / CTranslate2 model files (size + per-user choice)
# scripts/make_portable_zip.ps1 packages the build output together with a
# README that points users at the docs for fetching those external pieces.

# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(os.environ.get("PULPIT_INK_ROOT", os.getcwd())).resolve()
ENTRY = str(PROJECT_ROOT / "src" / "pulpit_ink" / "app" / "main.py")

# Keep ``src`` on sys.path so the analysis pass resolves
# ``pulpit_ink.*`` modules without an installed wheel.
SRC_DIR = str(PROJECT_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


hidden_imports = [
    "pulpit_ink.core.audio.enhancement_presets",
    "pulpit_ink.core.audio.ffmpeg_runner",
    "pulpit_ink.core.export.json_exporter",
    "pulpit_ink.core.export.markdown_exporter",
    "pulpit_ink.core.export.srt_exporter",
    "pulpit_ink.core.export.txt_exporter",
    "pulpit_ink.core.export.vtt_exporter",
    "pulpit_ink.core.postprocess.bible_refs",
    "pulpit_ink.core.postprocess.lexicon",
    "pulpit_ink.core.postprocess.pipeline",
    "pulpit_ink.core.reference.aligner",
    "pulpit_ink.core.reference.corrections",
    "pulpit_ink.core.reference.parser",
    "pulpit_ink.core.reference.prompt_builder",
    "pulpit_ink.core.transcription.faster_whisper_engine",
    "pulpit_ink.ui.main_window",
    "pulpit_ink.ui.transcript_editor",
    "pulpit_ink.ui.worker",
]

excludes = [
    # Avoid pulling in heavy ML toolkits we don't use.
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
    name="PulpitInk",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    name="PulpitInk",
)
