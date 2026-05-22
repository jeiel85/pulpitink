import { useEffect, useState } from "react";
import { Sparkles, X, ExternalLink } from "lucide-react";
import { openUrl } from "@tauri-apps/plugin-opener";
import { sidecarSyncJson } from "../lib/sidecar";
import type { UpdateCheckResult } from "../lib/types";

const DISMISS_KEY = "pulpitink-update-dismissed";

export function UpdateBanner() {
  const [result, setResult] = useState<UpdateCheckResult | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    sidecarSyncJson<UpdateCheckResult>(["update-check", "--json"])
      .then((r) => {
        setResult(r);
        const stored = localStorage.getItem(DISMISS_KEY);
        if (stored && stored === r.latest_version) {
          setDismissed(true);
        }
      })
      .catch(() => {
        // silent — update check is best-effort
      });
  }, []);

  if (!result || !result.has_update || dismissed || result.error) return null;

  function handleDismiss() {
    setDismissed(true);
    if (result) localStorage.setItem(DISMISS_KEY, result.latest_version);
  }

  return (
    <div className="update-banner">
      <Sparkles size={18} />
      <div className="update-banner-text">
        <strong>새 버전이 출시되었습니다!</strong>
        <span>
          {result.current_version} → {result.latest_version}
        </span>
      </div>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <button
          type="button"
          className="btn btn-primary"
          style={{ padding: "0.4rem 0.9rem", fontSize: "0.82rem" }}
          onClick={() => openUrl(result.download_url).catch(() => {})}
        >
          <ExternalLink size={12} />
          릴리즈 보기
        </button>
        <button type="button" className="icon-btn" onClick={handleDismiss} title="닫기">
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
