# API 合約：Session 管理

**基底路徑**：`/api/sessions`

---

## POST /api/sessions

建立新的工作階段，回傳 session_id。

**請求**：無 body

**回應** `201 Created`：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2026-07-02T13:30:00Z"
}
```

---

## DELETE /api/sessions/{session_id}

手動清除工作階段（關閉頁面時由前端觸發）。刪除所有關聯 PDF 檔案、ChromaDB Collections。

**路徑參數**：
- `session_id`：String (UUID)

**回應** `204 No Content`：無 body

**回應** `404 Not Found`：
```json
{"detail": "Session not found"}
```

---

## GET /api/sessions/{session_id}

取得工作階段狀態（可選，供前端驗證 session 是否有效）。

**路徑參數**：
- `session_id`：String (UUID)

**回應** `200 OK`：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "pdf_count": 2,
  "expires_at": "2026-07-02T13:30:00Z"
}
```
