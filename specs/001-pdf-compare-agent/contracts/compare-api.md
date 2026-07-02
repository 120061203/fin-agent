# API 合約：比較分析

**基底路徑**：`/api/sessions/{session_id}/compare`

---

## POST /api/sessions/{session_id}/compare

建立比較任務並立即開始執行。回傳 job_id，前端使用此 ID 訂閱 SSE 串流。

**請求** `application/json`：
```json
{
  "pdf_id_a": "7f3e1a2b-4c5d-6e7f-8a9b-0c1d2e3f4a5b",
  "pdf_id_b": "8a4b2c3d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
}
```

**回應** `202 Accepted`：
```json
{
  "job_id": "9b0c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  "status": "running",
  "stream_url": "/api/sessions/{session_id}/compare/9b0c3d4e-.../stream"
}
```

**錯誤回應**：

`400 Bad Request`（兩個 PDF ID 相同）：
```json
{"detail": "pdf_id_a and pdf_id_b must be different"}
```

`409 Conflict`（PDF 尚未完成前處理）：
```json
{"detail": "PDF 7f3e1a2b is not ready (status: processing)"}
```

---

## GET /api/sessions/{session_id}/compare/{job_id}/stream

Server-Sent Events 串流端點，回傳推理過程與最終報告。

**回應 Header**：
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**詳細事件格式**：見 [sse-events.md](./sse-events.md)

---

## GET /api/sessions/{session_id}/compare/{job_id}

取得比較任務狀態與最終報告（非串流版，供頁面重整後恢復）。

**回應** `200 OK`：
```json
{
  "job_id": "9b0c3d4e-...",
  "status": "done",
  "pdf_id_a": "7f3e1a2b-...",
  "pdf_id_b": "8a4b2c3d-...",
  "report_markdown": "# 比較報告\n\n## 服務範圍\n...",
  "completed_at": "2026-07-02T12:05:30Z"
}
```

**回應**（進行中）`200 OK`：
```json
{
  "job_id": "9b0c3d4e-...",
  "status": "running",
  "pdf_id_a": "7f3e1a2b-...",
  "pdf_id_b": "8a4b2c3d-...",
  "report_markdown": null,
  "completed_at": null
}
```
