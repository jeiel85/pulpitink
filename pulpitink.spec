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

PROJECT_ROOT = Path(os.environ.get("PULPITINK_ROOT", os.getcwd())).resolve()
ENTRY = str(PROJECT_ROOT / "src" / "pulpitink" / "app" / "main.py")

# Keep ``src`` on sys.path so the analysis pass resolves
# ``pulpitink.*`` modules without an installed wheel.
SRC_DIR = str(PROJECT_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


hidden_imports = [
    "pulpitink.core.audio.enhancement_presets",
    "pulpitink.core.audio.ffmpeg_runner",
    "pulpitink.core.export.json_exporter",
    "pulpitink.core.export.markdown_exporter",
    "pulpitink.core.export.srt_exporter",
    "pulpitink.core.export.txt_exporter",
    "pulpitink.core.export.vtt_exporter",
    "pulpitink.core.postprocess.bible_refs",
    "pulpitink.core.postprocess.lexicon",
    "pulpitink.core.postprocess.pipeline",
    "pulpitink.core.reference.aligner",
    "pulpitink.core.reference.corrections",
    "pulpitink.core.reference.parser",
    "pulpitink.core.reference.prompt_builder",
    "pulpitink.core.transcription.faster_whisper_engine",
    "pulpitink.ui.main_window",
    "pulpitink.ui.transcript_editor",
    "pulpitink.ui.worker",
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
