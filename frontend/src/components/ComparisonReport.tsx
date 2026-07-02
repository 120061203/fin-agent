import React from "react";
import ReactMarkdown from "react-markdown";

interface Props {
  markdown: string;
}

export function ComparisonReport({ markdown }: Props) {
  if (!markdown) return null;

  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ color: "#2d3748" }}>📋 比較報告</h3>
      <div
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: 8,
          padding: 24,
          background: "#fff",
          lineHeight: 1.7,
        }}
      >
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
}
