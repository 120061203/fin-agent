import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
        className="md-report"
      >
        <style>{`
          .md-report table { border-collapse: collapse; width: 100%; margin: 12px 0; }
          .md-report th, .md-report td { border: 1px solid #e2e8f0; padding: 6px 12px; text-align: left; }
          .md-report th { background: #f7fafc; font-weight: 600; }
          .md-report tr:nth-child(even) td { background: #fafafa; }
        `}</style>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
}
