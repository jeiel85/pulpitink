# PyInstaller spec for SermonScript (Windows portable build).
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

PROJECT_ROOT = Path(os.environ.get("SERMONSCRIPT_ROOT", os.getcwd())).resolve()
ENTRY = str(PROJECT_ROOT / "src" / "sermonscript" / "app" / "main.py")

# Keep ``src`` on sys.path so the analysis pass resolves
# ``sermonscript.*`` modules without an installed wheel.
SRC_DIR = str(PROJECT_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


hidden_imports = [
    "sermonscript.core.audio.enhancement_presets",
    "sermonscript.core.audio.ffmpeg_runner",
    "sermonscript.core.export.json_exporter",
    "sermonscript.core.export.markdown_exporter",
    "sermonscript.core.export.srt_exporter",
    "sermonscript.core.export.txt_exporter",
    "sermonscript.core.export.vtt_exporter",
    "sermonscript.core.postprocess.bible_refs",
    "sermonscript.core.postprocess.lexicon",
    "sermonscript.core.postprocess.pipeline",
    "sermonscript.core.reference.aligner",
    "sermonscript.core.reference.corrections",
    "sermonscript.core.reference.parser",
    "sermonscript.core.reference.prompt_builder",
    "sermonscript.core.transcription.faster_whisper_engine",
    "sermonscript.ui.main_window",
    "sermonscript.ui.transcript_editor",
    "sermonscript.ui.worker",
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
    name="SermonScript",
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
    name="SermonScript",
)
