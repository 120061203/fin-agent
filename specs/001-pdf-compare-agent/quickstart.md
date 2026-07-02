# 驗證指南：大型 PDF 文件比較 Agent

**日期**：2026-07-02
**對應計畫**：[plan.md](./plan.md)

---

## 先決條件

- Docker & Docker Compose 已安裝（Docker Engine 24+）
- 兩份測試用 PDF 文件（至少 10 頁，建議使用財務報表）
- LiteLLM Proxy 端點可存取：`https://lllm.xsong.us`
- 有效的 API Key

---

## 環境設定

在專案根目錄建立 `.env` 檔案：

```bash
LITELLM_BASE_URL=https://lllm.xsong.us
LITELLM_API_KEY=your_api_key_here
LITELLM_MODEL=claude-sonnet-4-6
```

---

## 啟動服務

```bash
docker compose up --build
```

等待看到以下輸出表示服務就緒：
```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | [nginx] started
```

服務位址：
- 前端：`http://localhost:3000`
- 後端 API 文件：`http://localhost:8000/docs`

---

## 驗證情境 1：端對端主流程（對應使用者故事 1）

**目標**：驗證上傳兩份 PDF → AI Agent 比較 → 串流推理 → 差異報告的完整流程。

**步驟**：

1. 開啟 `http://localhost:3000`
2. 點選「上傳 PDF」，選取第一份 PDF（至少 10 頁）
3. 等待上傳狀態顯示「就緒」（綠色）
4. 點選「上傳 PDF」，選取第二份 PDF
5. 等待兩份文件均顯示「就緒」
6. 勾選兩份文件，點選「開始比較分析」
7. 觀察推理步驟即時出現於畫面（應在 5 秒內出現第一則）
8. 等待分析完成（視文件大小而定）

**預期結果**：
- ✅ 推理步驟訊息逐步出現，包含 `info`、`thinking`、`result` 三種類型
- ✅ 最終差異報告顯示，包含「相同點」、「差異點」、「風險提示」三個區塊
- ✅ 整個流程無錯誤訊息

---

## 驗證情境 2：重複比較（對應使用者故事 2）

**目標**：驗證同一 Session 可多次選取不同 PDF 組合。

**步驟**（接續情境 1）：

1. 上傳第三份 PDF
2. 等待「就緒」
3. 取消勾選第二份 PDF，勾選第三份 PDF
4. 點選「開始比較分析」

**預期結果**：
- ✅ 舊報告清空，新的推理過程從頭顯示
- ✅ 分析使用正確的兩份文件（第一份 + 第三份）

---

## 驗證情境 3：Session 清除（對應使用者故事 3）

**目標**：驗證關閉頁面後 PDF 自動清除。

**步驟**：

1. 上傳至少一份 PDF，確認就緒
2. 記錄 Session ID（可從 Network tab 查看 Cookie/LocalStorage）
3. 關閉瀏覽器分頁
4. 等待 5 秒

**驗證方式**（二選一）：

**A. API 驗證**：
```bash
curl http://localhost:8000/api/sessions/{session_id}
# 預期回應：404 Not Found
```

**B. 檔案系統驗證**：
```bash
docker compose exec backend ls /tmp/sessions/
# 預期：目錄不存在或為空
```

**預期結果**：
- ✅ Session 已標記為 `cleaned`
- ✅ `/tmp/sessions/{session_id}/` 目錄已刪除

---

## 驗證情境 4：掃描版 PDF（對應 FR-002）

**目標**：驗證掃描版 PDF 能正確處理。

**步驟**：

1. 準備一份掃描版 PDF（可用 `img2pdf` 將圖片轉換）
2. 上傳此 PDF
3. 觀察上傳後的文件詳情

**API 驗證**：
```bash
curl http://localhost:8000/api/sessions/{session_id}/pdfs
# 確認 ocr_used: true
```

**預期結果**：
- ✅ `ocr_used: true`
- ✅ `status: "ready"`（OCR 完成後）
- ✅ `chunk_count > 0`

---

## API 快速測試（使用 curl）

```bash
# 1. 建立 Session
SESSION=$(curl -s -X POST http://localhost:8000/api/sessions | jq -r '.session_id')
echo "Session ID: $SESSION"

# 2. 上傳 PDF
PDF_A=$(curl -s -X POST \
  -F "file=@/path/to/doc_a.pdf" \
  http://localhost:8000/api/sessions/$SESSION/pdfs | jq -r '.pdf_id')

PDF_B=$(curl -s -X POST \
  -F "file=@/path/to/doc_b.pdf" \
  http://localhost:8000/api/sessions/$SESSION/pdfs | jq -r '.pdf_id')

# 3. 等待前處理（輪詢）
sleep 10
curl -s http://localhost:8000/api/sessions/$SESSION/pdfs | jq '.pdfs[].status'

# 4. 發起比較
JOB=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"pdf_id_a\": \"$PDF_A\", \"pdf_id_b\": \"$PDF_B\"}" \
  http://localhost:8000/api/sessions/$SESSION/compare | jq -r '.job_id')

# 5. 訂閱 SSE 串流
curl -N http://localhost:8000/api/sessions/$SESSION/compare/$JOB/stream
```

---

## 常見問題排查

| 問題 | 可能原因 | 解決方式 |
|------|---------|---------|
| 上傳後狀態一直是 `processing` | OCR 處理大型 PDF 耗時 | 等待最多 60 秒；若超過，查看 `docker compose logs backend` |
| SSE 沒有訊息 | LiteLLM 連線失敗 | 確認 `.env` 中 `LITELLM_BASE_URL` 可存取 |
| 前端無法連接後端 | CORS 或 nginx 代理設定 | 確認透過 `http://localhost:3000/api/...` 存取（非直接 8000） |
| `OCR` 失敗 | pytesseract 缺少語言包 | 確認 Dockerfile 安裝了 `tesseract-ocr-chi-tra`（繁中語言包） |
