const BASE = "/api";

export interface PDFInfo {
  pdf_id: string;
  filename: string;
  file_size_bytes: number;
  page_count: number | null;
  status: "uploading" | "processing" | "ready" | "error";
  ocr_used: boolean | null;
  chunk_count: number | null;
  uploaded_at: string;
  error_message: string | null;
}

export interface JobInfo {
  job_id: string;
  status: string;
  pdf_id_a: string;
  pdf_id_b: string;
  report_markdown: string | null;
  completed_at: string | null;
}

export async function createSession(): Promise<{ session_id: string; expires_at: string }> {
  const res = await fetch(`${BASE}/sessions`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${BASE}/sessions/${sessionId}`, { method: "DELETE" });
}

export async function uploadPDF(
  sessionId: string,
  file: File
): Promise<{ pdf_id: string; filename: string; status: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/sessions/${sessionId}/pdfs`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function listPDFs(sessionId: string): Promise<{ pdfs: PDFInfo[] }> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/pdfs`);
  if (!res.ok) throw new Error("Failed to list PDFs");
  return res.json();
}

export async function startComparison(
  sessionId: string,
  pdfIdA: string,
  pdfIdB: string
): Promise<{ job_id: string; status: string; stream_url: string }> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pdf_id_a: pdfIdA, pdf_id_b: pdfIdB }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Comparison failed" }));
    throw new Error(err.detail || "Comparison failed");
  }
  return res.json();
}

export async function getJob(sessionId: string, jobId: string): Promise<JobInfo> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/compare/${jobId}`);
  if (!res.ok) throw new Error("Failed to get job");
  return res.json();
}
