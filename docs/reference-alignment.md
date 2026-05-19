# Reference-Assisted Transcription

## 1. 기능명

한국어 UI 이름:

```text
원문 대조 변환
```

영문 이름:

```text
Reference-assisted Transcription
```

## 2. 목적

설교 원문, 개요, 성경 본문을 STT 결과와 대조하여 성경 구절, 고유명사, 신학 용어의 교정 후보를 제안합니다.

## 3. 처리 흐름

```text
오디오 파일 입력
→ 설교 원문 입력
→ 원문에서 키워드/성경구절/고유명사 추출
→ initial_prompt 생성
→ STT 실행
→ STT 결과와 원문 정렬
→ 차이점 탐지
→ 교정 후보 생성
→ 사용자가 승인
```

## 4. 중요한 원칙

설교 원문은 정답지가 아니라 참고 자료입니다.

실제 발화와 원문이 다를 때는 실제 발화를 우선 보존합니다.

## 5. 자동 보정 가능한 항목

| 유형 | 자동 보정 가능성 |
|---|---|
| 성경책 이름 | 높음 |
| 장절 표기 | 높음 |
| 숫자 표기 | 높음 |
| 목회자 이름 | 중간 |
| 교회명 | 중간 |
| 신학 용어 | 중간 |
| 일반 문장 | 낮음 |

## 6. 자동 교정 금지 항목

- 설교자가 원고와 다르게 말한 일반 문장
- 원문에 없는 추가 설명
- 회중 반응
- 실제 발화로 보이는 삽입 표현

## 7. 데이터 구조

```sql
CREATE TABLE reference_documents (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    title TEXT,
    file_path TEXT,
    content TEXT,
    created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE alignment_pairs (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    reference_start_index INTEGER,
    reference_end_index INTEGER,
    similarity_score REAL,
    alignment_status TEXT
);
```

```sql
CREATE TABLE correction_suggestions (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    original_text TEXT NOT NULL,
    suggested_text TEXT NOT NULL,
    category TEXT,
    confidence REAL,
    status TEXT
);
```

## 8. 상태값

```text
pending
accepted
rejected
always_apply
```
