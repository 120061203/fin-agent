import React, { useEffect, useRef } from "react";
import type { ReasoningStep } from "../services/sse";

interface Props {
  steps: ReasoningStep[];
  isRunning: boolean;
}

const TYPE_STYLE: Record<string, React.CSSProperties> = {
  info: { color: "#718096", fontSize: 13 },
  thinking: {
    background: "#ebf4ff",
    color: "#2b6cb0",
    fontFamily: "monospace",
    padding: "6px 10px",
    borderRadius: 4,
    fontSize: 13,
    whiteSpace: "pre-wrap",
    display: "block",
  },
  result: { color: "#276749", fontWeight: 600, fontSize: 14 },
};

export function ReasoningStream({ steps, isRunning }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps]);

  if (steps.length === 0 && !isRunning) return null;

  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ marginBottom: 12, color: "#2d3748" }}>⚙️ AI 推理過程</h3>
      <div
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: 8,
          padding: 16,
          maxHeight: 400,
          overflowY: "auto",
          background: "#fafafa",
        }}
      >
        {steps.map((step) => (
          <div key={step.step} style={{ marginBottom: 10 }}>
            <span style={{ color: "#a0aec0", fontSize: 11, marginRight: 6 }}>[{step.step}]</span>
            <span style={TYPE_STYLE[step.type] ?? {}}>{step.content}</span>
          </div>
        ))}
        {isRunning && <div style={{ color: "#4a9eff", fontSize: 13 }}>⏳ 分析中...</div>}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
