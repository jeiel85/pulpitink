# Architecture

## 1. 전체 구조

```text
Desktop GUI / PySide6
        |
Application Services
        |
Processing Pipeline
        |
STT Engines
        |
Post Processing
        |
Storage / Export
```

## 2. 주요 모듈

```text
src/pulpitink/
  app/
  cli/
  ui/
  core/
    audio/
    transcription/
    postprocess/
    reference/
    export/
  services/
  storage/
```

## 3. 책임 분리

| 계층 | 책임 |
|---|---|
| UI | 화면, 입력, 진행률, 사용자 액션 |
| CLI | 명령행 인터페이스 |
| Services | 작업 흐름, 설정, 모델 관리 |
| Core | 오디오 처리, STT, 후처리, Export |
| Storage | SQLite, 작업 이력 |
| Resources | 아이콘, 테마, 템플릿 |

## 4. 핵심 원칙

- UI는 STT 로직을 직접 가지지 않습니다.
- CLI와 GUI는 같은 core/service 모듈을 사용합니다.
- 작업은 Job 단위로 관리합니다.
- 원본 파일은 수정하지 않습니다.
- 긴 작업은 worker thread 또는 background task로 실행합니다.
