import { open as openDialog, save as saveDialog } from "@tauri-apps/plugin-dialog";
import { FolderOpen } from "lucide-react";

interface PathPickerProps {
  value: string;
  onChange: (path: string) => void;
  placeholder?: string;
  mode?: "file" | "directory" | "save";
  filters?: { name: string; extensions: string[] }[];
  buttonLabel?: string;
  saveDefaultName?: string;
}

export function PathPicker({
  value,
  onChange,
  placeholder,
  mode = "file",
  filters,
  buttonLabel,
  saveDefaultName,
}: PathPickerProps) {
  async function handlePick() {
    try {
      if (mode === "save") {
        const result = await saveDialog({ defaultPath: saveDefaultName, filters });
        if (typeof result === "string") onChange(result);
        return;
      }
      const result = await openDialog({
        directory: mode === "directory",
        multiple: false,
        filters,
      });
      if (typeof result === "string") onChange(result);
    } catch (err) {
      console.error("dialog 열기 실패:", err);
    }
  }

  return (
    <div className="path-picker">
      <input
        type="text"
        className="form-input path-input"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      <button type="button" className="btn btn-secondary path-btn" onClick={handlePick}>
        <FolderOpen size={14} />
        <span>{buttonLabel ?? "찾아보기"}</span>
      </button>
    </div>
  );
}
