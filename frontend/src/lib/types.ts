export interface Job {
  id: string;
  title: string;
  source_path: string;
  status: string;
  model_name: string;
  engine: string;
  preset: string;
  language: string | null;
  duration_sec: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Segment {
  job_id: string;
  start_sec: number;
  end_sec: number;
  raw_text: string;
  clean_text: string;
  edited_text: string;
  avg_logprob: number;
  no_speech_prob: number;
  speaker: string | null;
  id?: number;
  needs_review?: number;
}

export interface CorrectionSuggestion {
  id: number;
  job_id: string;
  segment_id: number;
  kind: string;
  original_text: string;
  suggested_text: string;
  status: string;
}

export interface AppSettings {
  language: string;
  model: string;
  preset: string;
  output_dir: string;
  model_cache_dir: string;
  device: string;
  compute_type: string;
  fuzzy_matching_enabled: boolean;
  fuzzy_threshold: number;
}

export interface BatchItem {
  id: string;
  audio_path: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  status_text: string;
  error?: string;
}

export interface UpdateCheckResult {
  has_update: boolean;
  current_version: string;
  latest_version: string;
  download_url: string;
  error: string | null;
}

export interface UserDictListResult {
  path: string;
  entries: Record<string, string[]>;
}
