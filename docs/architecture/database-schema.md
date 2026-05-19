# Database Schema

Use SQLite.

## jobs

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    title TEXT,
    duration_sec REAL,
    language TEXT,
    model_name TEXT,
    engine TEXT,
    preset TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

## segments

```sql
CREATE TABLE segments (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    start_sec REAL NOT NULL,
    end_sec REAL NOT NULL,
    raw_text TEXT,
    clean_text TEXT,
    edited_text TEXT,
    avg_logprob REAL,
    no_speech_prob REAL,
    needs_review INTEGER DEFAULT 0,
    speaker TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
```

## reference_documents

```sql
CREATE TABLE reference_documents (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    title TEXT,
    file_path TEXT,
    content TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
```

## alignment_pairs

```sql
CREATE TABLE alignment_pairs (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    reference_start_index INTEGER,
    reference_end_index INTEGER,
    similarity_score REAL,
    alignment_status TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id),
    FOREIGN KEY(segment_id) REFERENCES segments(id)
);
```

## correction_suggestions

```sql
CREATE TABLE correction_suggestions (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    original_text TEXT NOT NULL,
    suggested_text TEXT NOT NULL,
    category TEXT,
    confidence REAL,
    status TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id),
    FOREIGN KEY(segment_id) REFERENCES segments(id)
);
```

## dictionary_terms

```sql
CREATE TABLE dictionary_terms (
    id TEXT PRIMARY KEY,
    canonical TEXT NOT NULL,
    variants TEXT NOT NULL,
    category TEXT,
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```
