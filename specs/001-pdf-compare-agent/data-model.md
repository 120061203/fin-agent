# 資料模型：大型 PDF 文件比較 Agent

**日期**：2026-07-02
**對應計畫**：[plan.md](./plan.md)

---

## 實體關係概覽

```
Session (1) ──── (N) PDFDocument
Session (1) ──── (N) ComparisonJob
ComparisonJob (N) ──── (2) PDFDocument
ComparisonJob (1) ──── (N) ReasoningStep
```

---

## 實體定義

### Session（工作階段）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `session_id` | `str` (UUID v4) | 主鍵，由後端生成 |
| `created_at` | `datetime` | 建立時間（UTC） |
| `last_active_at` | `datetime` | 最後活動時間（UTC），用於 TTL 計算 |
| `expires_at` | `datetime` | 到期時間 = `last_active_at + 30min` |
| `upload_dir` | `str` | 本機暫存目錄路徑（如 `/tmp/sessions/{session_id}/`） |
| `status` | `enum` | `active` \| `expired` \| `cleaned` |

**狀態轉換**：`active` → `expired`（TTL 到期） → `cleaned`（資源刪除完成）

---

### PDFDocument（PDF 文件）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `pdf_id` | `str` (UUID v4) | 主鍵 |
| `session_id` | `str` | 外鍵，關聯 Session |
| `filename` | `str` | 原始檔名（如 `annual_report_2024.pdf`） |
| `file_path` | `str` | 本機暫存路徑 |
| `file_size_bytes` | `int` | 檔案大小 |
| `page_count` | `int` | 總頁數（抽取後填入） |
| `status` | `enum` | `uploading` \| `processing` \| `ready` \| `error` |
| `ocr_used` | `bool` | 是否啟用 OCR（預設 `false`） |
| `chunk_count` | `int` | 分段數量（前處理後填入） |
| `chroma_collection` | `str` | 對應的 ChromaDB Collection 名稱 |
| `uploaded_at` | `datetime` | 上傳時間（UTC） |
| `error_message` | `str \| None` | 錯誤訊息（狀態為 error 時填入） |

**驗證規則**：
- `file_size_bytes` ≤ 104,857,600（100MB）
- `filename` 副檔名必須為 `.pdf`
- 每個 Session 最多 10 份文件

---

### ComparisonJob（比較任務）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `job_id` | `str` (UUID v4) | 主鍵 |
| `session_id` | `str` | 外鍵，關聯 Session |
| `pdf_id_a` | `str` | 第一份文件 ID |
| `pdf_id_b` | `str` | 第二份文件 ID |
| `status` | `enum` | `queued` \| `running` \| `done` \| `error` |
| `created_at` | `datetime` | 任務建立時間（UTC） |
| `completed_at` | `datetime \| None` | 完成時間（UTC） |
| `report_markdown` | `str \| None` | 最終差異報告（Markdown 格式） |
| `error_message` | `str \| None` | 錯誤訊息 |

**驗證規則**：
- `pdf_id_a` ≠ `pdf_id_b`
- 兩份 PDF 的 `status` 必須均為 `ready` 才能建立任務
- 兩份 PDF 必須屬於同一個 `session_id`

---

### ReasoningStep（推理步驟）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `step_id` | `int` | 步驟序號（自動遞增） |
| `job_id` | `str` | 外鍵，關聯 ComparisonJob |
| `type` | `enum` | `info` \| `thinking` \| `result` |
| `content` | `str` | 步驟說明文字（顯示於前端） |
| `timestamp` | `datetime` | 發生時間（UTC） |

**type 語意**：
- `info`：系統狀態訊息（如「正在抽取文件…」）
- `thinking`：AI 推理過程（如「發現以下比較主題：…」）
- `result`：單一主題比較完成（如「主題【服務範圍】比較完成」）

---

### Chunk（PDF 分段，ChromaDB 內部結構）

> 此實體存於 ChromaDB，不在後端 Python 記憶體中持久化。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `chunk_id` | `str` | ChromaDB document ID（`{pdf_id}_chunk_{n}`） |
| `content` | `str` | 分段文字內容 |
| `page_start` | `int` | 起始頁碼 |
| `page_end` | `int` | 結束頁碼 |
| `section_title` | `str \| None` | 所屬章節標題 |
| `token_count` | `int` | 估算 token 數（tiktoken） |

---

## 儲存層設計

| 儲存類型 | 用途 | 生命週期 |
|---------|------|---------|
| 本機檔案系統 `/tmp/sessions/{session_id}/` | 儲存上傳的 PDF 原始檔 | Session 結束後刪除 |
| Python dict（記憶體） | Session、PDFDocument、ComparisonJob 物件 | 程序重啟後消失 |
| ChromaDB（記憶體模式） | PDF 分段向量索引 | Session 結束後刪除 Collection |

> **MVP 設計決策**：不使用資料庫，所有狀態保存於記憶體。若程序重啟，Session 資料遺失屬預期行為（面試展示場景可接受）。
