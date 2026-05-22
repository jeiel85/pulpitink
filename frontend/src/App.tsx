import { useEffect, useMemo, useRef, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import {
  Settings,
  List,
  FileAudio,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Search,
  Plus,
  Database,
  Sparkles,
  Sun,
  Moon,
  HelpCircle,
  BookOpenText,
  Video,
  PlayCircle,
  X,
} from "lucide-react";
import { sidecarSync, sidecarSyncJson, sidecarSpawn } from "./lib/sidecar";
import type {
  Job,
  Segment,
  CorrectionSuggestion,
  AppSettings,
  BatchItem,
} from "./lib/types";
import { PathPicker } from "./components/PathPicker";
import { YouTubeDialog } from "./components/YouTubeDialog";
import { GlossaryTab } from "./components/GlossaryTab";
import { UpdateBanner } from "./components/UpdateBanner";
import { WaveformPlayer, type WaveformHandle } from "./components/WaveformPlayer";
import "./App.css";

type TabKey = "dashboard" | "transcribe" | "editor" | "glossary" | "settings";

const APP_VERSION = "v0.5.0";

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [theme, setTheme] = useState<"dark" | "light">(() =>
    localStorage.getItem("pulpitink-theme") === "light" ? "light" : "dark"
  );
  const [showOnboarding, setShowOnboarding] = useState(
    () => localStorage.getItem("pulpitink-onboarding") !== "done"
  );

  // Dashboard
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Transcribe setup
  const [audioPath, setAudioPath] = useState("");
  const [referencePath, setReferencePath] = useState("");
  const [userDictPath, setUserDictPath] = useState("");
  const [selectedModel, setSelectedModel] = useState("small");
  const [selectedPreset, setSelectedPreset] = useState("sermon");
  const [selectedLanguage] = useState("ko");
  const [isFuzzyEnabled, setIsFuzzyEnabled] = useState(true);
  const [fuzzyThreshold, setFuzzyThreshold] = useState(0.7);
  const [youtubeDialogOpen, setYoutubeDialogOpen] = useState(false);

  // Transcribing
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcribeProgress, setTranscribeProgress] = useState(0);
  const [sidecarLogs, setSidecarLogs] = useState<{ type: "out" | "err"; text: string }[]>([]);
  const [transcribeStatusText, setTranscribeStatusText] = useState("대기 중...");

  // Batch queue (sequential)
  const [batchItems, setBatchItems] = useState<BatchItem[]>([]);
  const batchProcessingRef = useRef(false);
  const currentBatchIdRef = useRef<string | null>(null);

  // Editor
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [corrections, setCorrections] = useState<CorrectionSuggestion[]>([]);
  const [referenceParagraphs, setReferenceParagraphs] = useState<string[]>([]);
  const [activeSegmentIndex, setActiveSegmentIndex] = useState<number | null>(null);
  const waveformRef = useRef<WaveformHandle>(null);

  // Settings
  const [settings, setSettings] = useState<AppSettings>({
    language: "ko",
    model: "small",
    preset: "sermon",
    output_dir: "",
    model_cache_dir: "",
    device: "auto",
    compute_type: "int8",
    fuzzy_matching_enabled: true,
    fuzzy_threshold: 0.7,
  });
  const [dbPath, setDbPath] = useState("");
  const [doctorReport, setDoctorReport] = useState<{ name: string; ok: boolean; detail: string }[]>([]);
  const [isDiagnosing, setIsDiagnosing] = useState(false);

  const logConsoleRef = useRef<HTMLDivElement>(null);

  // ---------- Effects ----------

  useEffect(() => {
    loadJobs();
    loadSettings();
    getDatabasePath();
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("pulpitink-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (logConsoleRef.current) {
      logConsoleRef.current.scrollTop = logConsoleRef.current.scrollHeight;
    }
  }, [sidecarLogs]);

  // Sidecar event listeners
  useEffect(() => {
    let unlistenStdout: (() => void) | undefined;
    let unlistenStderr: (() => void) | undefined;
    let unlistenTerminated: (() => void) | undefined;

    async function setupListeners() {
      unlistenStdout = await listen<string>("sidecar-stdout", (event) => {
        const text = event.payload;
        setSidecarLogs((prev) => prev.length > 500 ? [...prev.slice(-300), { type: "out", text }] : [...prev, { type: "out", text }]);

        const match = text.match(/(\d+)%/);
        if (match) {
          const pct = parseInt(match[1], 10);
          setTranscribeProgress(pct);
          if (currentBatchIdRef.current) {
            updateBatchItem(currentBatchIdRef.current, { progress: pct });
          }
        }
        const lower = text.toLowerCase();
        let status: string | null = null;
        if (lower.includes("enhancing") || lower.includes("전처리")) status = "오디오 전처리 필터 적용 중...";
        else if (lower.includes("transcribing") || lower.includes("stt")) status = "faster-whisper STT 변환 중...";
        else if (lower.includes("exporting") || lower.includes("내보내기")) status = "결과물 포맷팅 및 내보내기 중...";
        else if (lower.includes("downloading") || lower.includes("youtube")) status = "YouTube 오디오 다운로드 중...";
        if (status) {
          setTranscribeStatusText(status);
          if (currentBatchIdRef.current) {
            updateBatchItem(currentBatchIdRef.current, { status_text: status });
          }
        }
      });

      unlistenStderr = await listen<string>("sidecar-stderr", (event) => {
        setSidecarLogs((prev) =>
          prev.length > 500
            ? [...prev.slice(-300), { type: "err", text: event.payload }]
            : [...prev, { type: "err", text: event.payload }]
        );
      });

      unlistenTerminated = await listen<number | null>("sidecar-terminated", (event) => {
        setIsTranscribing(false);
        const exitCode = event.payload;
        const ok = exitCode === 0;
        if (ok) {
          setTranscribeProgress(100);
          setTranscribeStatusText("변환 완료! 성공적으로 저장되었습니다.");
        } else {
          setTranscribeStatusText(`변환 실패 (종료 코드: ${exitCode}). 로그를 확인하세요.`);
        }
        const batchId = currentBatchIdRef.current;
        if (batchId) {
          updateBatchItem(batchId, {
            status: ok ? "completed" : "failed",
            progress: ok ? 100 : 0,
            status_text: ok ? "완료" : `실패 (코드 ${exitCode})`,
            error: ok ? undefined : `종료 코드 ${exitCode}`,
          });
          currentBatchIdRef.current = null;
          batchProcessingRef.current = false;
          loadJobs();
          setTimeout(() => processBatchQueue(), 200);
        } else {
          loadJobs();
        }
      });
    }

    setupListeners();
    return () => {
      unlistenStdout?.();
      unlistenStderr?.();
      unlistenTerminated?.();
    };
  }, []);

  // ---------- Data loaders ----------

  async function loadJobs() {
    setIsLoadingJobs(true);
    try {
      const parsed = await sidecarSyncJson<Job[]>(["jobs", "list", "--json"]);
      setJobs(parsed);
    } catch (err) {
      console.warn("jobs list 실패", err);
    } finally {
      setIsLoadingJobs(false);
    }
  }

  async function loadSettings() {
    try {
      const parsed = await sidecarSyncJson<AppSettings>(["settings", "show", "--json"]);
      setSettings(parsed);
      setSelectedModel(parsed.model || "small");
      setSelectedPreset(parsed.preset || "sermon");
      setIsFuzzyEnabled(parsed.fuzzy_matching_enabled ?? true);
      setFuzzyThreshold(parsed.fuzzy_threshold ?? 0.7);
    } catch (err) {
      console.warn("settings show 실패", err);
    }
  }

  async function getDatabasePath() {
    try {
      const output = await sidecarSync(["db-path"]);
      setDbPath(output.trim());
    } catch (err) {
      console.warn("db-path 실패", err);
    }
  }

  async function runDoctorDiagnostic() {
    setIsDiagnosing(true);
    setDoctorReport([]);
    try {
      const output = await sidecarSync(["doctor"]);
      const rows: { name: string; ok: boolean; detail: string }[] = [];
      output.split("\n").forEach((line) => {
        const cleanLine = line.replace(/\[[0-9;]*m/g, "");
        if (cleanLine.includes("OK") || cleanLine.includes("실패")) {
          const isOk = cleanLine.includes("OK");
          const parts = cleanLine.split("|").map((s) => s.trim()).filter(Boolean);
          rows.push({
            name: parts[0] || "진단 항목",
            ok: isOk,
            detail: parts.slice(2).join(" / ") || (isOk ? "정상" : "재확인 필요"),
          });
        }
      });
      setDoctorReport(rows.length ? rows : [{ name: "전체", ok: true, detail: "Doctor 명령이 정상 종료됨" }]);
    } catch (err) {
      setDoctorReport([{ name: "Doctor 실행 실패", ok: false, detail: String(err) }]);
    } finally {
      setIsDiagnosing(false);
    }
  }

  // ---------- Transcribe ----------

  function buildTranscribeArgs(source: string): string[] {
    const args = [
      "transcribe",
      source,
      "--model",
      selectedModel,
      "--preset",
      selectedPreset,
      "--language",
      selectedLanguage,
    ];
    if (referencePath) args.push("--reference", referencePath);
    if (userDictPath) args.push("--user-dict", userDictPath);
    args.push(isFuzzyEnabled ? "--fuzzy" : "--no-fuzzy");
    args.push("--fuzzy-threshold", fuzzyThreshold.toString());
    return args;
  }

  async function startTranscription() {
    if (!audioPath.trim()) {
      alert("오디오 파일 경로를 입력하거나 [찾아보기]로 선택하세요.");
      return;
    }
    enqueueBatch([audioPath.trim()]);
    setAudioPath("");
  }

  function enqueueBatch(paths: string[]) {
    const newItems: BatchItem[] = paths.map((p) => ({
      id: `batch_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      audio_path: p,
      status: "pending",
      progress: 0,
      status_text: "대기 중",
    }));
    setBatchItems((prev) => [...prev, ...newItems]);
    setTimeout(() => processBatchQueue(), 50);
  }

  function updateBatchItem(id: string, patch: Partial<BatchItem>) {
    setBatchItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)));
  }

  function removeBatchItem(id: string) {
    setBatchItems((prev) => prev.filter((it) => it.id !== id));
  }

  function clearCompletedBatches() {
    setBatchItems((prev) => prev.filter((it) => it.status === "pending" || it.status === "running"));
  }

  function processBatchQueue() {
    if (batchProcessingRef.current) return;
    setBatchItems((prev) => {
      const next = prev.find((it) => it.status === "pending");
      if (!next) return prev;
      batchProcessingRef.current = true;
      currentBatchIdRef.current = next.id;
      setIsTranscribing(true);
      setTranscribeProgress(0);
      setSidecarLogs([]);
      setTranscribeStatusText("변환 요청 중...");
      const args = buildTranscribeArgs(next.audio_path);
      sidecarSpawn(args).catch((err) => {
        const message = String(err);
        setSidecarLogs((logs) => [...logs, { type: "err", text: message }]);
        updateBatchItem(next.id, { status: "failed", error: message, status_text: "사이드카 호출 실패" });
        batchProcessingRef.current = false;
        currentBatchIdRef.current = null;
        setIsTranscribing(false);
        setTimeout(() => processBatchQueue(), 200);
      });
      return prev.map((it) =>
        it.id === next.id ? { ...it, status: "running", status_text: "변환 요청 중..." } : it
      );
    });
  }

  function handleYoutubeSubmit(url: string) {
    enqueueBatch([url]);
  }

  // ---------- Editor ----------

  async function loadJobIntoEditor(jobId: string) {
    try {
      const data = await sidecarSyncJson<{
        job: Job;
        segments: Segment[];
        corrections: CorrectionSuggestion[];
        reference?: { raw_content?: string } | null;
      }>(["jobs", "show", jobId, "--json"]);
      setSelectedJob(data.job);
      setSegments(data.segments);
      setCorrections(data.corrections);
      setActiveSegmentIndex(null);
      if (data.reference?.raw_content) {
        setReferenceParagraphs(
          data.reference.raw_content.split("\n\n").map((p) => p.trim()).filter(Boolean)
        );
      } else {
        setReferenceParagraphs([
          "이 작업에는 설교 원문이 첨부되지 않았습니다.",
          "변환 시 --reference 옵션으로 Markdown/TXT 파일을 등록하면 우측 패널에 원문이 표시됩니다.",
        ]);
      }
      setActiveTab("editor");
    } catch (err) {
      alert(`작업 상세 로딩 실패: ${String(err)}`);
    }
  }

  async function persistSegmentText(segment: Segment, text: string) {
    if (segment.id == null) return;
    try {
      await sidecarSyncJson([
        "segments",
        "update",
        String(segment.id),
        "--edited-text",
        text,
        "--json",
      ]);
    } catch (err) {
      console.error("segments update 실패", err);
    }
  }

  function handleSegmentChange(index: number, text: string) {
    setSegments((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], edited_text: text };
      persistSegmentText(updated[index], text);
      return updated;
    });
  }

  async function applyCorrection(
    suggestionId: number,
    segmentIndex: number,
    original: string,
    suggested: string
  ) {
    setCorrections((prev) => prev.map((c) => (c.id === suggestionId ? { ...c, status: "applied" } : c)));
    const segment = segments[segmentIndex];
    const currentText = segment.edited_text || segment.clean_text || segment.raw_text;
    const replaced = currentText.replace(original, suggested);
    handleSegmentChange(segmentIndex, replaced);
    try {
      await sidecarSyncJson(["corrections", "apply", String(suggestionId)]);
    } catch (err) {
      console.warn("corrections apply 실패", err);
    }
  }

  function seekToSegment(index: number) {
    setActiveSegmentIndex(index);
    const seg = segments[index];
    if (!seg) return;
    waveformRef.current?.seek(seg.start_sec);
  }

  function playSegmentRange(index: number) {
    const seg = segments[index];
    if (!seg) return;
    setActiveSegmentIndex(index);
    waveformRef.current?.playRange(seg.start_sec, seg.end_sec);
  }

  // ---------- Helpers ----------

  function formatTime(seconds: number): string {
    if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  function getStatusBadge(status: string) {
    const s = status.toLowerCase();
    if (s === "completed") return <span className="badge badge-success">완료</span>;
    if (s === "running") return <span className="badge badge-info">진행 중</span>;
    if (s === "failed") return <span className="badge badge-danger">실패</span>;
    return <span className="badge badge-warning">{status}</span>;
  }

  function dismissOnboarding() {
    localStorage.setItem("pulpitink-onboarding", "done");
    setShowOnboarding(false);
  }

  const filteredJobs = useMemo(() => {
    if (!searchQuery.trim()) return jobs;
    const q = searchQuery.toLowerCase();
    return jobs.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.source_path.toLowerCase().includes(q)
    );
  }, [jobs, searchQuery]);

  const batchSummary = useMemo(() => {
    const pending = batchItems.filter((it) => it.status === "pending").length;
    const running = batchItems.filter((it) => it.status === "running").length;
    const completed = batchItems.filter((it) => it.status === "completed").length;
    const failed = batchItems.filter((it) => it.status === "failed").length;
    return { pending, running, completed, failed };
  }, [batchItems]);

  // ---------- Render ----------

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div>
          <div className="brand-section">
            <div className="brand-logo">P</div>
            <h1 className="brand-name">PulpitInk</h1>
          </div>
          <nav className="nav-links">
            <NavItem icon={<List size={18} />} active={activeTab === "dashboard"} onClick={() => setActiveTab("dashboard")}>
              최근 작업 목록
            </NavItem>
            <NavItem icon={<FileAudio size={18} />} active={activeTab === "transcribe"} onClick={() => setActiveTab("transcribe")}>
              새 STT 변환
            </NavItem>
            <NavItem icon={<Sparkles size={18} />} active={activeTab === "editor"} onClick={() => setActiveTab("editor")}>
              검수 에디터
            </NavItem>
            <NavItem icon={<BookOpenText size={18} />} active={activeTab === "glossary"} onClick={() => setActiveTab("glossary")}>
              용어 사전
            </NavItem>
            <NavItem icon={<Settings size={18} />} active={activeTab === "settings"} onClick={() => setActiveTab("settings")}>
              설정 및 시스템
            </NavItem>
          </nav>
        </div>

        <div className="user-profile">
          <div className="avatar">PI</div>
          <div className="user-info">
            <span className="user-name">로컬 작업 공간</span>
            <span className="user-role">Private Desktop</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <UpdateBanner />

        <header className="header-bar">
          <div className="header-title">
            {activeTab === "dashboard" && <>최근 작업 대시보드</>}
            {activeTab === "transcribe" && <>새로운 설교 파일 STT 변환</>}
            {activeTab === "editor" && (
              <>
                <span>2단 대조 검수 편집기</span>
                {selectedJob && (
                  <span style={{ fontSize: "0.85rem", opacity: 0.6 }}>— {selectedJob.title}</span>
                )}
              </>
            )}
            {activeTab === "glossary" && <>사용자 용어 사전 (Glossary)</>}
            {activeTab === "settings" && <>시스템 상태 및 환경 설정</>}
          </div>

          <div className="header-actions">
            {activeTab === "dashboard" && (
              <button className="btn btn-outline" onClick={loadJobs}>
                <RefreshCw size={14} />
                <span>새로고침</span>
              </button>
            )}
            <button
              className="icon-btn"
              onClick={() => setShowOnboarding(true)}
              title="처음 시작 안내 다시 보기"
            >
              <HelpCircle size={18} />
            </button>
            <button
              className="icon-btn"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              title={theme === "dark" ? "라이트 테마로 전환" : "다크 테마로 전환"}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <span className="badge badge-accent">{APP_VERSION} Tauri Hybrid</span>
          </div>
        </header>

        <div className="content-body">
          {activeTab === "dashboard" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {showOnboarding && (
                <section className="onboarding-panel">
                  <div className="onboarding-copy">
                    <span className="eyebrow">처음 시작</span>
                    <h2>녹음 파일 하나로 변환, 검수, 내보내기까지 이어갑니다.</h2>
                    <p>
                      먼저 시스템 진단으로 로컬 환경을 확인하고, 오디오 파일이나 YouTube URL을 입력해 변환을 시작하세요.
                      변환이 끝나면 최근 작업에서 검수 에디터를 열 수 있습니다.
                    </p>
                  </div>
                  <div className="onboarding-steps">
                    <button className="onboarding-step" onClick={() => setActiveTab("settings")}>
                      <CheckCircle2 size={20} />
                      <span>
                        <strong>1. 시스템 진단</strong>
                        <small>FFmpeg, DB, 사이드카 확인</small>
                      </span>
                    </button>
                    <button className="onboarding-step" onClick={() => setActiveTab("transcribe")}>
                      <FileAudio size={20} />
                      <span>
                        <strong>2. 새 STT 변환</strong>
                        <small>오디오 파일/YouTube + 모델</small>
                      </span>
                    </button>
                    <button className="onboarding-step" onClick={dismissOnboarding}>
                      <ArrowRight size={20} />
                      <span>
                        <strong>안내 닫기</strong>
                        <small>필요하면 상단 ? 버튼으로 다시 열기</small>
                      </span>
                    </button>
                  </div>
                </section>
              )}

              <div className="glass-card flex-between" style={{ padding: "1rem 1.5rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", width: "50%" }}>
                  <Search size={18} style={{ color: "var(--text-secondary)" }} />
                  <input
                    type="text"
                    placeholder="작업 제목이나 원본 경로 검색..."
                    className="form-input"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ border: "none", padding: "0.5rem 0", background: "transparent" }}
                  />
                </div>
                <button className="btn btn-primary" onClick={() => setActiveTab("transcribe")}>
                  <Plus size={16} />
                  <span>새 작업 만들기</span>
                </button>
              </div>

              <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
                <div
                  className="job-item"
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    fontWeight: 600,
                    fontSize: "0.8rem",
                    color: "var(--text-secondary)",
                  }}
                >
                  <div>설교 제목 및 원본 오디오</div>
                  <div>STT 모델</div>
                  <div>전처리 프리셋</div>
                  <div>상태</div>
                  <div>기능</div>
                </div>

                {isLoadingJobs ? (
                  <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
                    <RefreshCw className="animate-spin" size={24} style={{ margin: "0 auto 1rem" }} />
                    <span>로컬 DB에서 최근 작업들을 로딩 중...</span>
                  </div>
                ) : filteredJobs.length === 0 ? (
                  <div className="empty-state">
                    <AlertTriangle size={34} />
                    <h3>아직 변환 작업이 없습니다.</h3>
                    <p>오디오 파일이나 YouTube URL을 준비한 뒤 첫 STT 변환을 시작하세요.</p>
                    <button className="btn btn-primary" onClick={() => setActiveTab("transcribe")}>
                      <Plus size={17} />
                      <span>첫 작업 만들기</span>
                    </button>
                  </div>
                ) : (
                  filteredJobs.map((job) => (
                    <div className="job-item" key={job.id}>
                      <div>
                        <div style={{ fontWeight: 600 }}>{job.title}</div>
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--text-muted)",
                            fontFamily: "var(--font-mono)",
                            marginTop: "0.25rem",
                            wordBreak: "break-all",
                          }}
                        >
                          {job.source_path}
                        </div>
                      </div>
                      <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
                        {job.model_name}
                      </div>
                      <div>{job.preset}</div>
                      <div>{getStatusBadge(job.status)}</div>
                      <div>
                        {job.status === "completed" ? (
                          <button
                            className="btn btn-outline"
                            style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
                            onClick={() => loadJobIntoEditor(job.id)}
                          >
                            검수 에디터 열기
                            <ArrowRight size={12} style={{ marginLeft: "0.4rem" }} />
                          </button>
                        ) : (
                          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>준비 중</span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === "transcribe" && (
            <div className="grid-2">
              <div className="glass-card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <h2
                  style={{
                    fontSize: "1.05rem",
                    fontWeight: 600,
                    borderBottom: "1px solid var(--border-light)",
                    paddingBottom: "0.75rem",
                  }}
                >
                  변환 파라미터 셋업
                </h2>

                <div className="form-group">
                  <label className="form-label">1. 원본 오디오 파일</label>
                  <PathPicker
                    value={audioPath}
                    onChange={setAudioPath}
                    placeholder="예: D:\Media\sermon_audio.mp3"
                    filters={[
                      {
                        name: "오디오/비디오",
                        extensions: ["mp3", "wav", "m4a", "aac", "flac", "ogg", "mp4"],
                      },
                    ]}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ alignSelf: "flex-start", marginTop: "0.5rem" }}
                    onClick={() => setYoutubeDialogOpen(true)}
                  >
                    <Video size={14} style={{ color: "#ef4444" }} />
                    YouTube URL로 변환
                  </button>
                </div>

                <div className="form-group">
                  <label className="form-label">2. 설교 원문 텍스트 파일 (선택)</label>
                  <PathPicker
                    value={referencePath}
                    onChange={setReferencePath}
                    placeholder="예: D:\Text\sermon_note.md"
                    filters={[{ name: "텍스트/마크다운", extensions: ["txt", "md", "markdown"] }]}
                  />
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    Markdown/TXT 원문을 대조해 자동 성경 교정 및 Fuzzy 매칭 후보를 추출합니다.
                  </span>
                </div>

                <div className="form-group">
                  <label className="form-label">3. 사용자 정의 용어 사전 (선택)</label>
                  <PathPicker
                    value={userDictPath}
                    onChange={setUserDictPath}
                    placeholder="비워두면 기본 사용자 사전 사용"
                    filters={[{ name: "JSON", extensions: ["json"] }]}
                  />
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">STT 연산 모델</label>
                    <select
                      className="form-select"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                    >
                      <option value="tiny">Tiny (가장 빠름)</option>
                      <option value="base">Base</option>
                      <option value="small">Small (권장)</option>
                      <option value="medium">Medium</option>
                      <option value="large-v3">Large v3 (최고 정확도)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">전처리 프리셋</label>
                    <select
                      className="form-select"
                      value={selectedPreset}
                      onChange={(e) => setSelectedPreset(e.target.value)}
                    >
                      <option value="none">전처리 없음</option>
                      <option value="stt_basic">기본 노이즈 리덕션</option>
                      <option value="sermon">목회자 설교 프리셋 (권장)</option>
                      <option value="noisy">노이즈가 심한 외부 녹음</option>
                    </select>
                  </div>
                </div>

                <div
                  style={{
                    background: "rgba(139, 92, 246, 0.05)",
                    border: "1px solid rgba(139, 92, 246, 0.15)",
                    borderRadius: "8px",
                    padding: "1rem",
                  }}
                >
                  <div className="flex-between" style={{ marginBottom: "0.5rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <Sparkles size={16} style={{ color: "var(--color-accent)" }} />
                      <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>한글 자모(Jamo) Fuzzy 매칭</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={isFuzzyEnabled}
                      onChange={(e) => setIsFuzzyEnabled(e.target.checked)}
                      style={{ cursor: "pointer", width: "16px", height: "16px" }}
                    />
                  </div>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                    STT 오인식(예: "이에수" → "예수")을 자모 구조 단위로 분석하는 Fuzzy Scorer 임계값을 제어합니다.
                  </p>
                  {isFuzzyEnabled && (
                    <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.75rem" }}>
                      <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>
                        임계값: {fuzzyThreshold.toFixed(2)}
                      </span>
                      <input
                        type="range"
                        min="0.60"
                        max="0.90"
                        step="0.05"
                        value={fuzzyThreshold}
                        onChange={(e) => setFuzzyThreshold(parseFloat(e.target.value))}
                        style={{ flex: 1, cursor: "pointer" }}
                      />
                    </div>
                  )}
                </div>

                <button
                  className="btn btn-primary"
                  onClick={startTranscription}
                  disabled={!audioPath.trim()}
                  style={{ width: "100%", padding: "0.85rem", marginTop: "0.25rem" }}
                >
                  <FileAudio size={16} />
                  <span>큐에 추가하고 변환 시작</span>
                </button>
              </div>

              <div className="glass-card" style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "450px" }}>
                <div className="flex-between" style={{ borderBottom: "1px solid var(--border-light)", paddingBottom: "0.75rem", marginBottom: "1rem" }}>
                  <h2 style={{ fontSize: "1.05rem", fontWeight: 600 }}>배치 큐 및 사이드카 콘솔</h2>
                  <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
                    {isTranscribing && (
                      <span className="badge badge-accent animate-pulse">{transcribeStatusText}</span>
                    )}
                    {batchItems.some((it) => it.status === "completed" || it.status === "failed") && (
                      <button className="btn btn-outline" style={{ padding: "0.3rem 0.6rem", fontSize: "0.75rem" }} onClick={clearCompletedBatches}>
                        완료/실패 정리
                      </button>
                    )}
                  </div>
                </div>

                {isTranscribing && (
                  <div className="progress-bg" style={{ height: "6px", marginBottom: "1rem" }}>
                    <div className="progress-fill" style={{ width: `${transcribeProgress}%` }}></div>
                  </div>
                )}

                {batchItems.length > 0 && (
                  <div className="batch-queue">
                    <div className="batch-summary">
                      <span>대기 {batchSummary.pending}</span>
                      <span>진행 {batchSummary.running}</span>
                      <span style={{ color: "var(--color-success)" }}>완료 {batchSummary.completed}</span>
                      {batchSummary.failed > 0 && (
                        <span style={{ color: "var(--color-danger)" }}>실패 {batchSummary.failed}</span>
                      )}
                    </div>
                    <div className="batch-list">
                      {batchItems.map((item) => (
                        <div key={item.id} className={`batch-item batch-${item.status}`}>
                          <div className="batch-item-main">
                            <div className="batch-item-path" title={item.audio_path}>
                              {item.audio_path}
                            </div>
                            <div className="batch-item-status">
                              {item.status === "running" && (
                                <RefreshCw size={12} className="animate-spin" />
                              )}
                              {item.status === "completed" && <CheckCircle2 size={12} />}
                              {item.status === "failed" && <AlertTriangle size={12} />}
                              <span>{item.status_text}</span>
                              {item.status === "running" && <span>· {item.progress}%</span>}
                            </div>
                          </div>
                          {(item.status === "pending" || item.status === "failed" || item.status === "completed") && (
                            <button
                              className="icon-btn batch-remove"
                              onClick={() => removeBatchItem(item.id)}
                              title="목록에서 제거"
                            >
                              <X size={12} />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div
                  className="log-console"
                  ref={logConsoleRef}
                  style={{ flex: 1, height: "300px", marginTop: batchItems.length > 0 ? "1rem" : 0 }}
                >
                  {sidecarLogs.length === 0 ? (
                    <div style={{ color: "var(--text-muted)", padding: "2rem", textAlign: "center" }}>
                      변환을 시작하면 백그라운드 Python 엔진(enhancement, faster-whisper, alignment)의 실시간 로그가 여기에 표시됩니다.
                    </div>
                  ) : (
                    sidecarLogs.map((log, i) => (
                      <div className={`log-line ${log.type === "err" ? "err" : ""}`} key={i}>
                        {log.text}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === "editor" && (
            <div style={{ height: "100%" }}>
              {!selectedJob ? (
                <div
                  className="glass-card"
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "6rem 2rem",
                    textAlign: "center",
                    color: "var(--text-muted)",
                  }}
                >
                  <Sparkles size={48} style={{ color: "var(--color-accent)", marginBottom: "1.5rem" }} />
                  <h2 style={{ fontSize: "1.25rem", color: "var(--text-primary)", fontWeight: 600, marginBottom: "0.5rem" }}>
                    검수 대상 작업 미지정
                  </h2>
                  <p>최근 작업 목록(Dashboard)에서</p>
                  <p>"검수 에디터 열기" 버튼을 통해 편집할 설교를 로드해 주세요.</p>
                </div>
              ) : (
                <div className="glass-card editor-shell">
                  <div className="editor-waveform">
                    <WaveformPlayer
                      ref={waveformRef}
                      audioPath={selectedJob.source_path}
                    />
                  </div>

                  <div className="editor-layout">
                    <div className="editor-left">
                      <div className="panel-header">
                        <span className="panel-title">STT 세그먼트 타임라인 ({segments.length})</span>
                        <span className="badge badge-success">DB 연결 정상</span>
                      </div>

                      <div className="panel-scroll">
                        {segments.map((seg, i) => {
                          const segId = seg.id ?? i + 1;
                          const segCorrections = corrections.filter(
                            (c) => c.segment_id === segId && c.status === "pending"
                          );
                          const isNeedsReview = seg.needs_review === 1;
                          return (
                            <div
                              className={`segment-card ${activeSegmentIndex === i ? "active" : ""}`}
                              key={segId}
                              onClick={() => seekToSegment(i)}
                              style={isNeedsReview ? { borderLeft: "3px solid var(--color-warning)" } : {}}
                            >
                              <div className="segment-meta">
                                <button
                                  type="button"
                                  className="timestamp"
                                  onDoubleClick={(e) => {
                                    e.stopPropagation();
                                    playSegmentRange(i);
                                  }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    seekToSegment(i);
                                  }}
                                  title="더블클릭: 이 구간만 재생 / 클릭: 위치 이동"
                                >
                                  {formatTime(seg.start_sec)} - {formatTime(seg.end_sec)}
                                </button>
                                {seg.speaker && <span className="badge">화자: {seg.speaker}</span>}
                                {isNeedsReview && (
                                  <span className="badge badge-warning" style={{ fontSize: "0.6rem" }}>
                                    검수 대상
                                  </span>
                                )}
                                <button
                                  type="button"
                                  className="icon-btn"
                                  style={{ width: 28, height: 28 }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    playSegmentRange(i);
                                  }}
                                  title="이 구간만 재생"
                                >
                                  <PlayCircle size={14} />
                                </button>
                              </div>
                              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                                <div
                                  style={{
                                    fontSize: "0.78rem",
                                    color: "var(--text-muted)",
                                    textDecoration: "line-through",
                                  }}
                                >
                                  {seg.raw_text}
                                </div>
                                <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                                  {seg.clean_text}
                                </div>
                                <textarea
                                  className="segment-editor"
                                  value={seg.edited_text !== "" ? seg.edited_text : seg.clean_text}
                                  onChange={(e) => handleSegmentChange(i, e.target.value)}
                                  placeholder="검수 편집 텍스트 입력..."
                                  rows={2}
                                  onClick={(e) => e.stopPropagation()}
                                />
                              </div>

                              {segCorrections.length > 0 && (
                                <div className="correction-bubble">
                                  <div className="correction-bubble-head">
                                    <Sparkles size={12} />
                                    <span>Fuzzy 매칭 교정 제안:</span>
                                  </div>
                                  <div className="correction-bubble-list">
                                    {segCorrections.map((corr) => (
                                      <button
                                        key={corr.id}
                                        type="button"
                                        className="correction-pill"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          applyCorrection(corr.id, i, corr.original_text, corr.suggested_text);
                                        }}
                                      >
                                        "{corr.original_text}" →{" "}
                                        <strong style={{ textDecoration: "underline" }}>
                                          {corr.suggested_text}
                                        </strong>
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="editor-right">
                      <div className="panel-header">
                        <span className="panel-title">설교 원문 대조 패널</span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>원문 하이라이트</span>
                      </div>
                      <div className="panel-scroll" style={{ backgroundColor: "rgba(0,0,0,0.15)" }}>
                        <div className="reference-content">
                          {referenceParagraphs.map((para, i) => {
                            const isMatched =
                              activeSegmentIndex !== null &&
                              segments[activeSegmentIndex] != null &&
                              (segments[activeSegmentIndex].clean_text.includes(para.slice(0, 8)) ||
                                para.includes(segments[activeSegmentIndex].clean_text.slice(0, 8)));
                            return (
                              <p
                                className={`reference-paragraph ${isMatched ? "matched" : ""}`}
                                key={i}
                              >
                                {para}
                              </p>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="editor-footer">
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      더블클릭으로 구간 재생 · 텍스트 수정 시 자동 저장
                    </span>
                    <button
                      className="btn btn-primary"
                      style={{ padding: "0.5rem 1rem", fontSize: "0.85rem" }}
                      onClick={async () => {
                        try {
                          await sidecarSync(["jobs", "export", selectedJob.id]);
                          alert("검수 수정본이 export 디렉터리에 다시 저장되었습니다.");
                        } catch (err) {
                          alert(`Export 실패: ${String(err)}`);
                        }
                      }}
                    >
                      검수 완료 및 Export 실행
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "glossary" && <GlossaryTab />}

          {activeTab === "settings" && (
            <div className="grid-2">
              <div className="glass-card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <h2
                  style={{
                    fontSize: "1.05rem",
                    fontWeight: 600,
                    borderBottom: "1px solid var(--border-light)",
                    paddingBottom: "0.75rem",
                  }}
                >
                  Tauri + Python Sidecar 환경 설정
                </h2>

                <div className="form-group">
                  <label className="form-label">기본 SQLite DB 저장 위치</label>
                  <div
                    style={{
                      backgroundColor: "rgba(0,0,0,0.3)",
                      border: "1px solid var(--border-light)",
                      borderRadius: "8px",
                      padding: "0.75rem 1rem",
                      fontSize: "0.8rem",
                      fontFamily: "var(--font-mono)",
                      wordBreak: "break-all",
                    }}
                  >
                    {dbPath || "(로딩 중)"}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">기본 STT 모델 디렉토리 경로</label>
                  <PathPicker
                    value={settings.model_cache_dir}
                    onChange={(p) => setSettings({ ...settings, model_cache_dir: p })}
                    placeholder="비워두면 %LOCALAPPDATA%/PulpitInk/models 사용"
                    mode="directory"
                  />
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">기본 언어</label>
                    <select
                      className="form-select"
                      value={settings.language}
                      onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                    >
                      <option value="ko">한국어 (ko)</option>
                      <option value="en">English (en)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">추론 디바이스</label>
                    <select
                      className="form-select"
                      value={settings.device}
                      onChange={(e) => setSettings({ ...settings, device: e.target.value })}
                    >
                      <option value="auto">Auto (자동 최적화)</option>
                      <option value="cpu">CPU 전용</option>
                      <option value="cuda">GPU (NVIDIA CUDA)</option>
                    </select>
                  </div>
                </div>

                <button
                  className="btn btn-primary"
                  onClick={async () => {
                    try {
                      await sidecarSync(["settings", "set", "model", settings.model]);
                      await sidecarSync(["settings", "set", "preset", settings.preset]);
                      await sidecarSync(["settings", "set", "language", settings.language]);
                      await sidecarSync(["settings", "set", "device", settings.device]);
                      alert("사용자 설정이 저장되었습니다.");
                    } catch (err) {
                      alert(`설정 저장 실패: ${String(err)}`);
                    }
                  }}
                  style={{ width: "100%", padding: "0.75rem" }}
                >
                  <Database size={16} />
                  <span>설정 정보 영속화 저장</span>
                </button>
              </div>

              <div className="glass-card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="flex-between" style={{ borderBottom: "1px solid var(--border-light)", paddingBottom: "0.75rem" }}>
                  <h2 style={{ fontSize: "1.05rem", fontWeight: 600 }}>PulpitInk Doctor 시스템 진단</h2>
                  <button
                    className="btn btn-outline"
                    style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
                    onClick={runDoctorDiagnostic}
                    disabled={isDiagnosing}
                  >
                    {isDiagnosing ? "진단 중..." : "새 진단 실행"}
                  </button>
                </div>

                {isDiagnosing ? (
                  <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
                    <RefreshCw className="animate-spin" size={24} style={{ margin: "0 auto 1rem" }} />
                    <span>로컬 컴퓨터 환경을 진단하고 있습니다...</span>
                  </div>
                ) : doctorReport.length === 0 ? (
                  <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
                    "새 진단 실행" 버튼을 누르시면 로컬 PC의 파이썬 코어 상태, FFmpeg 디바이스 호환 여부, SQLite 데이터 호환성을 정합 검사합니다.
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {doctorReport.map((row, i) => (
                      <div
                        className="flex-between"
                        key={i}
                        style={{
                          padding: "0.75rem 1rem",
                          backgroundColor: "rgba(255,255,255,0.02)",
                          border: "1px solid var(--border-light)",
                          borderRadius: "8px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                          {row.ok ? (
                            <CheckCircle2 size={16} style={{ color: "var(--color-success)" }} />
                          ) : (
                            <AlertTriangle size={16} style={{ color: "var(--color-warning)" }} />
                          )}
                          <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>{row.name}</span>
                        </div>
                        <span
                          style={{
                            fontSize: "0.8rem",
                            color: "var(--text-secondary)",
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {row.detail}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <YouTubeDialog
        open={youtubeDialogOpen}
        onClose={() => setYoutubeDialogOpen(false)}
        onSubmit={handleYoutubeSubmit}
      />
    </div>
  );
}

function NavItem({
  icon,
  active,
  onClick,
  children,
}: {
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>
      {icon}
      <span>{children}</span>
    </div>
  );
}

export default App;
