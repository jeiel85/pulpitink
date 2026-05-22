import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import WaveSurfer from "wavesurfer.js";
import { convertFileSrc } from "@tauri-apps/api/core";
import { Play, Pause, Volume2 } from "lucide-react";

export interface WaveformHandle {
  seek(seconds: number): void;
  playRange(start: number, end: number): void;
  togglePlay(): void;
}

interface WaveformPlayerProps {
  audioPath: string | null;
  onTimeUpdate?: (sec: number) => void;
  onReady?: (duration: number) => void;
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "00:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export const WaveformPlayer = forwardRef<WaveformHandle, WaveformPlayerProps>(
  ({ audioPath, onTimeUpdate, onReady }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WaveSurfer | null>(null);
    const playRangeRef = useRef<{ start: number; end: number } | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [duration, setDuration] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [loadError, setLoadError] = useState<string | null>(null);

    useEffect(() => {
      if (!containerRef.current) return;
      const ws = WaveSurfer.create({
        container: containerRef.current,
        waveColor: "rgba(96, 165, 250, 0.55)",
        progressColor: "#0ea5e9",
        cursorColor: "#f3f4f6",
        cursorWidth: 2,
        height: 64,
        barWidth: 2,
        barRadius: 1,
        barGap: 1,
        normalize: true,
        interact: true,
      });
      wsRef.current = ws;

      ws.on("ready", () => {
        const dur = ws.getDuration();
        setDuration(dur);
        setLoadError(null);
        if (onReady) onReady(dur);
      });
      ws.on("play", () => setIsPlaying(true));
      ws.on("pause", () => setIsPlaying(false));
      ws.on("finish", () => setIsPlaying(false));
      ws.on("timeupdate", (sec) => {
        setCurrentTime(sec);
        if (onTimeUpdate) onTimeUpdate(sec);
        const range = playRangeRef.current;
        if (range && sec >= range.end) {
          ws.pause();
          playRangeRef.current = null;
        }
      });
      ws.on("error", (err) => {
        setLoadError(typeof err === "string" ? err : "오디오 로드 실패");
      });

      return () => {
        ws.destroy();
        wsRef.current = null;
      };
    }, []);

    useEffect(() => {
      const ws = wsRef.current;
      if (!ws) return;
      if (!audioPath) {
        ws.empty();
        setDuration(0);
        setCurrentTime(0);
        setLoadError(null);
        return;
      }
      try {
        const url = convertFileSrc(audioPath);
        ws.load(url);
        setLoadError(null);
      } catch (err) {
        setLoadError(`오디오 경로 변환 실패: ${err}`);
      }
    }, [audioPath]);

    useImperativeHandle(ref, () => ({
      seek(seconds: number) {
        const ws = wsRef.current;
        if (!ws || duration <= 0) return;
        const pos = Math.max(0, Math.min(seconds, duration)) / duration;
        ws.seekTo(pos);
      },
      playRange(start: number, end: number) {
        const ws = wsRef.current;
        if (!ws || duration <= 0) return;
        playRangeRef.current = { start, end };
        const pos = Math.max(0, Math.min(start, duration)) / duration;
        ws.seekTo(pos);
        ws.play();
      },
      togglePlay() {
        const ws = wsRef.current;
        if (!ws) return;
        ws.playPause();
      },
    }));

    return (
      <div className="waveform-player">
        <div className="waveform-controls">
          <button
            className="play-btn"
            type="button"
            onClick={() => wsRef.current?.playPause()}
            disabled={!audioPath || loadError !== null}
            title={isPlaying ? "일시정지" : "재생"}
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>
          <Volume2 size={18} style={{ color: "var(--text-secondary)" }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
        <div ref={containerRef} className="waveform-canvas" />
        {!audioPath && (
          <div className="waveform-placeholder">
            오디오 파일이 연결되어 있지 않습니다. 작업의 원본 경로가 유효해야 파형이 표시됩니다.
          </div>
        )}
        {loadError && (
          <div className="waveform-placeholder" style={{ color: "var(--color-danger)" }}>
            ⚠ {loadError}
          </div>
        )}
      </div>
    );
  }
);

WaveformPlayer.displayName = "WaveformPlayer";
