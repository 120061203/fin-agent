import React, { useEffect, useRef, useState } from "react";
import { createSession, listPDFs, startComparison } from "./services/api";
import type { PDFInfo } from "./services/api";
import { subscribeToStream } from "./services/sse";
import type { ReasoningStep } from "./services/sse";
import { PDFUpload } from "./components/PDFUpload";
import { PDFList } from "./components/PDFList";
import { ReasoningStream } from "./components/ReasoningStream";
import { ComparisonReport } from "./components/ComparisonReport";

const SESSION_KEY = "pdf_compare_session_id";

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pdfs, setPdfs] = useState<PDFInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [steps, setSteps] = useState<ReasoningStep[]>([]);
  const [report, setReport] = useState<string>("");
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const closeStreamRef = useRef<(() => void) | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Initialize session
  useEffect(() => {
    const init = async () => {
      let sid = sessionStorage.getItem(SESSION_KEY);
      if (!sid) {
        try {
          const { session_id } = await createSession();
          sid = session_id;
          sessionStorage.setItem(SESSION_KEY, sid);
        } catch {
          console.error("Failed to create session");
          return;
        }
      }
      setSessionId(sid);
    };
    init();

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // Cleanup on page close (US3)
  useEffect(() => {
    const handleUnload = () => {
      const sid = sessionStorage.getItem(SESSION_KEY);
      if (sid) {
        navigator.sendBeacon(`/api/sessions/${sid}/cleanup`);
        sessionStorage.removeItem(SESSION_KEY);
      }
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, []);

  const refreshPDFs = async (sid: string) => {
    try {
      const { pdfs: list } = await listPDFs(sid);
      setPdfs(list);
      return list;
    } catch {
      return [];
    }
  };

  const startPolling = (sid: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const list = await refreshPDFs(sid);
      if (list.every((p: PDFInfo) => p.status === "ready" || p.status === "error")) {
        clearInterval(pollRef.current!);
        pollRef.current = null;
      }
    }, 2000);
  };

  const handleUploaded = () => {
    if (!sessionId) return;
    refreshPDFs(sessionId);
    startPolling(sessionId);
  };

  const handleCompare = async () => {
    if (!sessionId || selectedIds.length !== 2) return;

    // Reset state (US2: supports re-selection)
    setError(null);
    setSteps([]);
    setReport("");
    setIsRunning(true);

    if (closeStreamRef.current) {
      closeStreamRef.current();
      closeStreamRef.current = null;
    }

    try {
      const { job_id } = await startComparison(sessionId, selectedIds[0], selectedIds[1]);
      const close = subscribeToStream(sessionId, job_id, {
        onReasoningStep: (step) => setSteps((prev) => [...prev, step]),
        onReport: (md) => setReport(md),
        onDone: () => setIsRunning(false),
        onError: (msg) => {
          setError(msg);
          setIsRunning(false);
        },
      });
      closeStreamRef.current = close;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "比較失敗");
      setIsRunning(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 900,
        margin: "0 auto",
        padding: "32px 16px",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <h1 style={{ color: "#1a202c", marginBottom: 4 }}>📊 PDF 財務文件比較 Agent</h1>
      <p style={{ color: "#718096", marginBottom: 32, marginTop: 0 }}>
        上傳兩份大型 PDF，透過 AI Agent 進行比較分析（支援掃描版 OCR）
      </p>

      {!sessionId && <p style={{ color: "#718096" }}>初始化中...</p>}

      {sessionId && (
        <>
          <PDFUpload sessionId={sessionId} onUploaded={handleUploaded} />

          {pdfs.length > 0 && (
            <PDFList
              pdfs={pdfs}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          )}

          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 12 }}>
            <button
              onClick={handleCompare}
              disabled={selectedIds.length !== 2 || isRunning}
              style={{
                background: selectedIds.length === 2 && !isRunning ? "#4a9eff" : "#a0aec0",
                color: "#fff",
                border: "none",
                borderRadius: 6,
                padding: "10px 24px",
                fontSize: 15,
                cursor: selectedIds.length === 2 && !isRunning ? "pointer" : "not-allowed",
                fontWeight: 600,
              }}
            >
              {isRunning ? "⏳ 分析中..." : "🔍 開始比較分析"}
            </button>
            {selectedIds.length !== 2 && (
              <span style={{ color: "#718096", fontSize: 13 }}>
                請從上方勾選 2 份就緒的 PDF
              </span>
            )}
          </div>

          {error && (
            <div
              style={{
                marginTop: 16,
                padding: 12,
                background: "#fff5f5",
                border: "1px solid #fc8181",
                borderRadius: 6,
                color: "#c53030",
              }}
            >
              ⚠️ {error}
              <button
                onClick={handleCompare}
                style={{
                  marginLeft: 12,
                  background: "transparent",
                  border: "1px solid #fc8181",
                  borderRadius: 4,
                  padding: "2px 8px",
                  cursor: "pointer",
                  color: "#c53030",
                  fontSize: 12,
                }}
              >
                重試
              </button>
            </div>
          )}

          <ReasoningStream steps={steps} isRunning={isRunning} />
          <ComparisonReport markdown={report} />
        </>
      )}
    </div>
  );
}
