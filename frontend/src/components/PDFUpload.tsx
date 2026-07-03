import React, { useRef, useState } from "react";
import { uploadPDF } from "../services/api";

interface Props {
  sessionId: string;
  onUploaded: () => void;
}

export function PDFUpload({ sessionId, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploads, setUploads] = useState<{ name: string; percent: number }[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const list = Array.from(files);
    const invalid = list.find((f) => !f.name.toLowerCase().endsWith(".pdf"));
    if (invalid) {
      setError("請選擇 PDF 檔案");
      return;
    }
    setError(null);
    setUploads(list.map((f) => ({ name: f.name, percent: 0 })));
    for (let i = 0; i < list.length; i++) {
      try {
        await uploadPDF(sessionId, list[i], (percent) => {
          setUploads((prev) => prev.map((u, idx) => (idx === i ? { ...u, percent } : u)));
        });
        onUploaded();
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "上傳失敗");
        setUploads([]);
        return;
      }
    }
    setUploads([]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const isUploading = uploads.length > 0;

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      style={{
        border: "2px dashed #4a9eff",
        borderRadius: 8,
        padding: 24,
        textAlign: "center",
        cursor: isUploading ? "default" : "pointer",
        background: "#f0f7ff",
      }}
      onClick={() => { if (!isUploading) inputRef.current?.click(); }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        multiple
        style={{ display: "none" }}
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
      {isUploading ? (
        <div>
          {uploads.map((u) => (
            <div key={u.name} style={{ marginBottom: 8 }}>
              <p style={{ margin: "0 0 4px", fontSize: 13, color: "#333" }}>{u.name}</p>
              <div style={{ background: "#dde", borderRadius: 4, overflow: "hidden", height: 8 }}>
                <div
                  style={{
                    width: `${u.percent}%`,
                    height: "100%",
                    background: "#4a9eff",
                    transition: "width 0.2s",
                  }}
                />
              </div>
              <p style={{ margin: "2px 0 0", fontSize: 12, color: "#4a9eff" }}>{u.percent}%</p>
            </div>
          ))}
        </div>
      ) : (
        <>
          <p style={{ margin: 0, fontWeight: 600 }}>📄 拖放 PDF 或點選上傳（可多選）</p>
          <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>
            支援純文字及掃描版 PDF，上限 500MB
          </p>
        </>
      )}
      {error && <p style={{ color: "#e53e3e", marginTop: 8, margin: "8px 0 0" }}>{error}</p>}
    </div>
  );
}
