import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, Video } from "lucide-react";
import { sidecarSync, sidecarSyncJson } from "../lib/sidecar";

interface YouTubeDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (url: string) => void;
}

export function YouTubeDialog({ open, onClose, onSubmit }: YouTubeDialogProps) {
  const [url, setUrl] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [installErr, setInstallErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setUrl("");
    setAgreed(false);
    setInstallErr(null);
    sidecarSyncJson<{ available: boolean }>(["youtube", "check", "--json"])
      .then((r) => setAvailable(r.available))
      .catch(() => setAvailable(false));
  }, [open]);

  async function installYtDlp() {
    setBusy(true);
    setInstallErr(null);
    try {
      const result = await sidecarSyncJson<{ ok: boolean; already?: boolean }>(
        ["youtube", "install", "--json"]
      );
      setAvailable(result.ok || !!result.already);
      if (!result.ok && !result.already) {
        setInstallErr("yt-dlp 설치 실패. 수동 설치가 필요합니다.");
      }
    } catch (err: unknown) {
      setInstallErr(`yt-dlp 설치 중 오류: ${String(err)}`);
      try {
        await sidecarSync(["youtube", "check", "--json"]);
      } catch {
        /* noop */
      }
    } finally {
      setBusy(false);
    }
  }

  if (!open) return null;

  const urlOk = /^https?:\/\/(www\.|m\.|music\.)?(youtube\.com|youtu\.be)\//i.test(url.trim());
  const canSubmit = agreed && available && urlOk;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-window" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <Video size={20} style={{ color: "#ef4444" }} />
          <h2>YouTube URL 변환 (Opt-in)</h2>
        </div>

        <div className="modal-body">
          <div className="disclaimer-block">
            <AlertTriangle size={18} />
            <div>
              <p>
                YouTube 음원 다운로드는 <b>저작권자가 허용한 콘텐츠</b>(자신이 업로드한 설교, 공개 강의 등)에 한해
                사용해야 합니다. DRM/접근 제한 우회, 로그인 기반 수집, 클라우드 재업로드는 지원하지 않습니다.
              </p>
              <p style={{ marginTop: "0.5rem" }}>
                다운로드된 오디오는 <code>cache/jobs/&lt;id&gt;</code>에 임시 저장되며,
                작업 삭제 시 함께 제거됩니다.
              </p>
            </div>
          </div>

          <label className="form-label">YouTube URL</label>
          <input
            type="text"
            className="form-input"
            value={url}
            placeholder="https://www.youtube.com/watch?v=..."
            onChange={(e) => setUrl(e.target.value)}
            spellCheck={false}
          />

          <div className="yt-dlp-status">
            {available === null && (
              <span className="badge badge-info">yt-dlp 상태 확인 중...</span>
            )}
            {available === true && (
              <span className="badge badge-success">
                <CheckCircle2 size={12} style={{ marginRight: 4 }} />
                yt-dlp 설치됨
              </span>
            )}
            {available === false && (
              <div className="yt-dlp-missing">
                <span className="badge badge-warning">
                  <AlertTriangle size={12} style={{ marginRight: 4 }} />
                  yt-dlp 미설치
                </span>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={installYtDlp}
                  disabled={busy}
                  style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
                >
                  {busy ? (
                    <>
                      <RefreshCw className="animate-spin" size={12} /> 설치 중...
                    </>
                  ) : (
                    "pip로 자동 설치"
                  )}
                </button>
              </div>
            )}
            {installErr && (
              <p style={{ color: "var(--color-danger)", fontSize: "0.78rem", marginTop: "0.5rem" }}>
                {installErr}
              </p>
            )}
          </div>

          <label className="agreement">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
            />
            <span>
              위 저작권/이용 약관에 동의하며, 해당 콘텐츠를 합법적으로 사용할 권한이 있음을 확인합니다.
            </span>
          </label>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-outline" onClick={onClose}>
            취소
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!canSubmit}
            onClick={() => {
              onSubmit(url.trim());
              onClose();
            }}
          >
            동의하고 변환 시작
          </button>
        </div>
      </div>
    </div>
  );
}
