import { useEffect, useState } from "react";
import { Plus, Search, Trash2, Upload, Download, RefreshCw, BookOpenText } from "lucide-react";
import { save as saveDialog, open as openDialog } from "@tauri-apps/plugin-dialog";
import { sidecarSyncJson } from "../lib/sidecar";
import type { UserDictListResult } from "../lib/types";

export function GlossaryTab() {
  const [entries, setEntries] = useState<Record<string, string[]>>({});
  const [dictPath, setDictPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [newCanonical, setNewCanonical] = useState("");
  const [newWrong, setNewWrong] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const result = await sidecarSyncJson<UserDictListResult>(["user-dict", "list", "--json"]);
      setEntries(result.entries);
      setDictPath(result.path);
    } catch (err) {
      setMessage(`사전 로딩 실패: ${String(err)}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleAdd() {
    const canonical = newCanonical.trim();
    if (!canonical) return;
    const wrongForms = newWrong
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    setBusy(true);
    setMessage(null);
    try {
      await sidecarSyncJson(["user-dict", "add", canonical, ...wrongForms, "--json"]);
      setNewCanonical("");
      setNewWrong("");
      await refresh();
      setMessage(`추가됨: ${canonical}`);
    } catch (err) {
      setMessage(`추가 실패: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(canonical: string) {
    setBusy(true);
    try {
      await sidecarSyncJson(["user-dict", "remove", canonical, "--json"]);
      await refresh();
      setMessage(`삭제됨: ${canonical}`);
    } catch (err) {
      setMessage(`삭제 실패: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleImport() {
    try {
      const result = await openDialog({
        multiple: false,
        directory: false,
        filters: [{ name: "CSV", extensions: ["csv"] }],
      });
      if (typeof result !== "string") return;
      setBusy(true);
      const r = await sidecarSyncJson<{ imported: number; total: number }>(
        ["user-dict", "import", result, "--json"]
      );
      await refresh();
      setMessage(`CSV 가져오기 완료: ${r.imported}개 (총 ${r.total}개)`);
    } catch (err) {
      setMessage(`가져오기 실패: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    try {
      const result = await saveDialog({
        defaultPath: "pulpitink-glossary.csv",
        filters: [{ name: "CSV", extensions: ["csv"] }],
      });
      if (typeof result !== "string") return;
      setBusy(true);
      const r = await sidecarSyncJson<{ exported: number }>(
        ["user-dict", "export", result, "--json"]
      );
      setMessage(`CSV 내보내기 완료: ${r.exported}개 → ${result}`);
    } catch (err) {
      setMessage(`내보내기 실패: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  const filtered = Object.entries(entries).filter(([canonical, forms]) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      canonical.toLowerCase().includes(q) ||
      forms.some((f) => f.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <div className="glass-card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div className="flex-between">
          <h2 style={{ fontSize: "1.05rem", fontWeight: 600, display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <BookOpenText size={18} /> 사용자 용어 사전 (Glossary)
          </h2>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button className="btn btn-outline" onClick={refresh} disabled={loading || busy}>
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              새로고침
            </button>
            <button className="btn btn-secondary" onClick={handleImport} disabled={busy}>
              <Upload size={14} />
              CSV 가져오기
            </button>
            <button className="btn btn-secondary" onClick={handleExport} disabled={busy}>
              <Download size={14} />
              CSV 내보내기
            </button>
          </div>
        </div>

        <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          저장 위치: {dictPath || "(로딩 중)"}
        </div>

        <div className="glossary-add-row">
          <input
            type="text"
            className="form-input"
            placeholder="표준 단어 (예: 예수 그리스도)"
            value={newCanonical}
            onChange={(e) => setNewCanonical(e.target.value)}
            disabled={busy}
          />
          <input
            type="text"
            className="form-input"
            placeholder="STT 오인식 후보 (쉼표/공백 구분)"
            value={newWrong}
            onChange={(e) => setNewWrong(e.target.value)}
            disabled={busy}
          />
          <button
            className="btn btn-primary"
            onClick={handleAdd}
            disabled={!newCanonical.trim() || busy}
          >
            <Plus size={14} />
            추가/갱신
          </button>
        </div>

        {message && (
          <div className="badge badge-info" style={{ alignSelf: "flex-start" }}>
            {message}
          </div>
        )}
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "1rem 1.5rem", borderBottom: "1px solid var(--border-light)" }}>
          <Search size={16} style={{ color: "var(--text-secondary)" }} />
          <input
            type="text"
            className="form-input"
            placeholder="검색 (표준 단어 또는 오인식 후보)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ border: "none", padding: "0.5rem 0", background: "transparent" }}
          />
          <span className="badge">{filtered.length} / {Object.keys(entries).length}</span>
        </div>

        {loading ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
            <RefreshCw className="animate-spin" size={22} style={{ margin: "0 auto 1rem" }} />
            <div>사전을 불러오는 중...</div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <BookOpenText size={32} />
            <h3>등록된 사전 항목이 없습니다</h3>
            <p>윗쪽의 입력 칸으로 표준 단어와 STT 오인식 후보를 추가해 보세요.</p>
          </div>
        ) : (
          <div className="glossary-table">
            <div className="glossary-row glossary-row-head">
              <div>표준 단어</div>
              <div>STT 오인식 후보</div>
              <div></div>
            </div>
            {filtered.map(([canonical, forms]) => (
              <div className="glossary-row" key={canonical}>
                <div style={{ fontWeight: 600 }}>{canonical}</div>
                <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
                  {forms.length === 0 ? "—" : forms.join(", ")}
                </div>
                <div>
                  <button
                    className="icon-btn"
                    onClick={() => handleRemove(canonical)}
                    title="삭제"
                    disabled={busy}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
