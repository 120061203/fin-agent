# API 合約：PDF 管理

**基底路徑**：`/api/sessions/{session_id}/pdfs`

---

## POST /api/sessions/{session_id}/pdfs

上傳一份 PDF 文件，並啟動非同步前處理（抽取、OCR 判斷、Chunking、向量索引）。

**請求**：`multipart/form-data`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `file` | File | PDF 檔案（.pdf，上限 100MB） |

**回應** `202 Accepted`（前處理非同步進行）：
```json
{
  "pdf_id": "7f3e1a2b-4c5d-6e7f-8a9b-0c1d2e3f4a5b",
  "filename": "annual_report_2024.pdf",
  "file_size_bytes": 5242880,
  "status": "processing"
}
```

**錯誤回應**：

`400 Bad Request`（格式錯誤）：
```json
{"detail": "Only PDF files are accepted"}
```

`413 Request Entity Too Large`（超過 100MB）：
```json
{"detail": "File size exceeds 100MB limit"}
```

`409 Conflict`（超過 10 份）：
```json
{"detail": "Session PDF limit (10) reached"}
```

---

## GET /api/sessions/{session_id}/pdfs

列出該 Session 已上傳的所有 PDF 文件。

**回應** `200 OK`：
```json
{
  "pdfs": [
    {
      "pdf_id": "7f3e1a2b-...",
      "filename": "annual_report_2024.pdf",
      "file_size_bytes": 5242880,
      "page_count": 120,
      "status": "ready",
      "ocr_used": false,
      "chunk_count": 45,
      "uploaded_at": "2026-07-02T12:00:00Z"
    },
    {
      "pdf_id": "8a4b2c3d-...",
      "filename": "annual_report_2023.pdf",
      "file_size_bytes": 4831838,
      "page_count": 115,
      "status": "processing",
      "ocr_used": null,
      "chunk_count": null,
      "uploaded_at": "2026-07-02T12:01:00Z"
    }
  ]
}
```

---

## DELETE /api/sessions/{session_id}/pdfs/{pdf_id}

刪除單一 PDF 文件及其向量索引。

**回應** `204 No Content`：無 body

**回應** `404 Not Found`：
```json
{"detail": "PDF not found"}
```
