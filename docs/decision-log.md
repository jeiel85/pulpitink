# Decision Log

## 2026-05-20: PC 데스크톱 우선

결정:
- SermonScript는 Windows PC 데스크톱 앱으로 먼저 개발합니다.

근거:
- 긴 설교 녹음 처리에는 PC의 CPU/GPU, 메모리, 파일 관리, 편집 UI가 유리합니다.
- 모바일은 녹음/확인/공유 보조 앱으로 나중에 검토합니다.

## 2026-05-20: Python + PySide6 채택

결정:
- Python 3.11+, PySide6, faster-whisper, FFmpeg, SQLite 조합을 사용합니다.

근거:
- STT, 오디오, 후처리 생태계가 Python 중심입니다.
- CLI와 GUI를 같은 core 모듈로 재사용하기 쉽습니다.

## 2026-05-20: YouTube URL 입력 후순위

결정:
- YouTube URL 입력은 v1.0에서 제외하고 v1.5 또는 v2.0 후보로 둡니다.

근거:
- 저작권/이용 권한 리스크가 있습니다.
- 핵심 로컬 파일 STT 파이프라인 안정화가 먼저입니다.
- 나중에 input source 계층으로 분리 구현하면 됩니다.
