import React, { useRef, useState } from "react";
import { uploadPDF } from "../services/api";

interface Props {
  sessionId: string;
  onUploaded: () => void;
}

export function PDFUpload({ sessionId, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("請選擇 PDF 檔案");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await uploadPDF(sessionId, file);
      onUploaded();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "上傳失敗");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      style={{
        border: "2px dashed #4a9eff",
        borderRadius: 8,
        padding: 24,
        textAlign: "center",
        cursor: "pointer",
        background: "#f0f7ff",
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
      {uploading ? (
        <p style={{ color: "#4a9eff", margin: 0 }}>上傳中...</p>
      ) : (
        <>
          <p style={{ margin: 0, fontWeight: 600 }}>📄 拖放 PDF 或點選上傳</p>
          <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>
            支援純文字及掃描版 PDF，上限 100MB
          </p>
        </>
      )}
      {error && <p style={{ color: "#e53e3e", marginTop: 8, margin: "8px 0 0" }}>{error}</p>}
    </div>
  );
}
