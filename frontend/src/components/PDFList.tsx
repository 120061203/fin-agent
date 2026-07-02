import React from "react";
import type { PDFInfo } from "../services/api";

interface Props {
  pdfs: PDFInfo[];
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
}

const STATUS_LABELS: Record<string, { text: string; color: string }> = {
  uploading: { text: "上傳中", color: "#ed8936" },
  processing: { text: "處理中", color: "#4a9eff" },
  ready: { text: "就緒", color: "#38a169" },
  error: { text: "錯誤", color: "#e53e3e" },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function PDFList({ pdfs, selectedIds, onSelectionChange }: Props) {
  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((x) => x !== id));
    } else if (selectedIds.length < 2) {
      onSelectionChange([...selectedIds, id]);
    }
  };

  return (
    <div style={{ marginTop: 20 }}>
      <h3 style={{ color: "#2d3748", marginBottom: 8 }}>
        已上傳的文件（勾選 2 份進行比較）
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {pdfs.map((pdf) => {
          const isSelected = selectedIds.includes(pdf.pdf_id);
          const isReady = pdf.status === "ready";
          const isDisabled = !isReady || (!isSelected && selectedIds.length >= 2);
          const statusInfo = STATUS_LABELS[pdf.status] ?? { text: pdf.status, color: "#718096" };

          return (
            <div
              key={pdf.pdf_id}
              onClick={() => !isDisabled && toggle(pdf.pdf_id)}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "10px 14px",
                border: `2px solid ${isSelected ? "#4a9eff" : "#e2e8f0"}`,
                borderRadius: 8,
                background: isSelected ? "#ebf4ff" : "#fff",
                cursor: isDisabled ? "not-allowed" : "pointer",
                opacity: isDisabled && !isSelected ? 0.5 : 1,
                transition: "all 0.15s",
              }}
            >
              <input
                type="checkbox"
                checked={isSelected}
                readOnly
                disabled={isDisabled}
                style={{ marginRight: 12, width: 16, height: 16 }}
                onClick={(e) => e.stopPropagation()}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: "#2d3748" }}>{pdf.filename}</div>
                <div style={{ fontSize: 12, color: "#718096", marginTop: 2 }}>
                  {formatBytes(pdf.file_size_bytes)}
                  {pdf.page_count ? ` · ${pdf.page_count} 頁` : ""}
                  {pdf.ocr_used ? " · OCR 處理" : ""}
                  {pdf.chunk_count ? ` · ${pdf.chunk_count} 段落` : ""}
                </div>
              </div>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: statusInfo.color,
                  background: `${statusInfo.color}20`,
                  padding: "2px 8px",
                  borderRadius: 12,
                  flexShrink: 0,
                }}
              >
                {statusInfo.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
