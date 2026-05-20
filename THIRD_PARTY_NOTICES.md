# Third Party Notices

이 파일은 릴리즈 전에 실제 사용 의존성 기준으로 반드시 갱신해야 합니다.
Goal 3 패키징 시점 기준으로 ``scripts/build_windows.ps1`` 가 PyInstaller
번들을 생성합니다. FFmpeg, STT 모델은 번들에 포함하지 않습니다.

## Runtime Dependencies (Wheel + PyInstaller bundle)

| Name | Purpose | Notice |
|---|---|---|
| Python | Runtime | Python Software Foundation License |
| PySide6 | GUI (옵션) | LGPL v3 — 동적 링크 유지, 자체 빌드 변경 금지 |
| faster-whisper | STT | MIT |
| CTranslate2 | STT 백엔드 | MIT |
| Typer | CLI | MIT |
| Rich | CLI 출력 | MIT |
| Pydantic | 데이터 검증 | MIT |
| platformdirs | 사용자 경로 | MIT |
| RapidFuzz | 원문 대조 (옵션) | MIT |

## Development-only Dependencies (번들 미포함)

| Name | Purpose | Notice |
|---|---|---|
| pytest | 테스트 러너 | MIT |
| ruff | 린트 | MIT |
| PyInstaller | 번들러 | GPL-2.0-or-later with bootloader exception |

## External Binaries Required at Runtime (not bundled)

| Component | Why excluded | User action |
|---|---|---|
| FFmpeg | LGPL/GPL 빌드 옵션이 배포 정책에 따라 달라 사용자가 직접 설치 | ``ffmpeg.exe`` / ``ffprobe.exe`` 를 PATH 또는 실행 폴더에 둘 것 |
| faster-whisper 모델 (`tiny`–`large-v3`) | 파일 크기, 사용자 선택권, huggingface 캐시 정책 | 최초 실행 시 자동 다운로드. 오프라인은 `sermonscript settings` 로 `model_cache_dir` 지정 |
| CUDA / cuDNN | NVIDIA 라이선스, 사용자 환경 의존 | 사용자가 해당 드라이버 설치 |

## Distribution Policy

- 모델 파일은 저장소 또는 배포 ZIP 에 포함하지 않습니다.
- FFmpeg 바이너리는 기본 배포에 포함하지 않습니다. 별도 번들 시 빌드 옵션과
  라이선스 (LGPL/GPL) 를 명시해야 합니다.
- PySide6 는 LGPL 동적 링크 형태로 사용합니다. Qt 자체를 정적 링크하거나
  수정 빌드를 배포하지 않습니다.
- 산출물: ``dist/SermonScript_Portable_{version}.zip``.
  내부 구조는 ``scripts/make_portable_zip.ps1`` 가 PORTABLE-README.txt 와
  함께 묶어 명시합니다.
