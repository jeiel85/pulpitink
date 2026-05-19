# Audio Pipeline

## 1. 목적

전처리의 목적은 사람이 듣기 좋은 음질을 만드는 것이 아니라, STT 모델이 인식하기 좋은 음성 신호를 만드는 것입니다.

## 2. 기본 흐름

```text
원본 오디오
→ 메타데이터 분석
→ 품질 분석
→ 전처리 프리셋 선택
→ processed.wav 생성
→ STT 입력
```

## 3. 프리셋

| 프리셋 | 설명 |
|---|---|
| none | 포맷 변환만 수행 |
| stt_basic | 안전한 기본 STT 최적화 |
| sermon | 설교 녹음용 균형 프리셋 |
| noisy | 잡음 많은 녹음용 강한 프리셋 |
| custom | 사용자가 수동 조정 |

## 4. FFmpeg 필터 예시

### stt_basic

```bash
highpass=f=80,lowpass=f=7800,loudnorm=I=-18:TP=-1.5:LRA=11
```

### sermon

```bash
highpass=f=80,lowpass=f=7500,afftdn=nf=-25,dynaudnorm=f=150:g=15,loudnorm=I=-18:TP=-1.5:LRA=11
```

### noisy

```bash
highpass=f=100,lowpass=f=6500,afftdn=nf=-30,dynaudnorm=f=200:g=20,loudnorm=I=-18:TP=-1.5:LRA=11
```

## 5. 주의

과한 전처리는 오히려 정확도를 낮출 수 있습니다.

- 노이즈 제거 과함: 자음 끝 손상
- 로우패스 과함: 발음 구분력 저하
- 압축 과함: 배경 잡음 증폭
- 무음 삭제: 타임스탬프 어긋남

## 6. 저장 정책

```text
cache/jobs/{job_id}/processed.wav
```

원본 파일은 절대 수정하지 않습니다.
