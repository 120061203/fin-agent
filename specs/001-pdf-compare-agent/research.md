# 研究報告：大型 PDF 文件比較 Agent

**日期**：2026-07-02
**對應計畫**：[plan.md](./plan.md)

---

## 決策 1：PDF 文字抽取策略

**決策**：以 `pdfplumber` 作為主要抽取工具，`pymupdf`（fitz）作為備援，pytesseract OCR 作為掃描版最終手段。

**理由**：
- `pdfplumber` 對表格與多欄版面的解析品質最佳，且提供頁碼資訊
- `pymupdf` 速度較快，適合作為備援（部分 PDF 格式 pdfplumber 無法解析）
- 判斷是否需要 OCR 的標準：若抽取出的文字字元數 < 頁數 × 50，視為掃描版，啟用 OCR

**評估過的替代方案**：
- `pypdf2`：維護停滯，不採用
- `camelot`：專注表格，通用性不足
- 直接用 LLM vision 處理掃描版：成本過高且超出 MVP 範圍

---

## 決策 2：Chunking 策略

**決策**：以章節/段落為單位進行語意切割，每個 chunk 上限 4,000 tokens（約 3,000 中文字）。

**理由**：
- 按章節切割確保每個 chunk 語意完整，向量搜尋相關性更高
- 4,000 tokens 留有足夠空間讓 LLM 在比較時接收兩份文件的 chunk（共 8,000 tokens）加上 system prompt
- 頁碼資訊保留在 chunk metadata 中，便於追溯

**章節識別規則**（優先順序）：
1. 正規表示式比對常見標題模式：`^\s*[第一二三四五六七八九十\d]+[章節條款]\s*`、`^\s*\d+\.\s+[A-Z\u4e00-\u9fff]`
2. 字型大小差異（pymupdf 提供）
3. 若上述均無法識別，以固定 3,000 字分段（Sliding Window，overlap 200 字）

---

## 決策 3：向量資料庫

**決策**：ChromaDB，記憶體模式（`ephemeral client`），每個 Session 建立兩個獨立 Collection（`doc_a_{session_id}`、`doc_b_{session_id}`）。

**理由**：
- MVP 不需要持久化，記憶體模式零配置
- Session 結束後直接刪除 Collection，完美契合「關閉頁面清除資料」需求
- 不需要額外 ChromaDB 伺服器，降低 Docker Compose 複雜度

**Embedding 策略**：
- 使用 LiteLLM 呼叫 embedding model（若可用）
- 備援：chromadb 內建 `all-MiniLM-L6-v2`（`sentence-transformers`）

---

## 決策 4：Agent 比較邏輯

**決策**：採用三步驟 Orchestrator 模式（非 LangGraph），以純 Python async 實作，降低依賴複雜度。

**步驟**：
1. **主題發現（Topic Discovery）**：傳送兩份文件各前 5 頁的文字給 LLM，產生比較主題列表（JSON 格式）
2. **逐主題比較（Per-Topic Comparison）**：對每個主題，從兩個 Collection 各取 Top-3 相關 chunks，呼叫 LLM 比較，輸出 `{相同點, 差異點, 風險提示}`
3. **彙整報告（Aggregation）**：合併所有主題結果，呼叫 LLM 生成最終 Markdown 報告

**理由**：
- LangGraph 對 MVP 而言過度複雜（原則一）
- 純 async Python 易於除錯和測試
- 三步驟可精確控制每步的 SSE 推理訊息

**評估過的替代方案**：
- LangGraph：功能強大但學習曲線高，超出 MVP 需求
- 單次大 prompt：無法處理大型 PDF（Context 限制）

---

## 決策 5：即時串流（SSE）

**決策**：使用 FastAPI 的 `StreamingResponse` 搭配 `text/event-stream`（Server-Sent Events）。

**理由**：
- SSE 比 WebSocket 實作簡單，單向串流完全符合需求（Server → Client）
- FastAPI 原生支援，無需額外套件
- 前端用 `EventSource` API 消費，瀏覽器原生支援

**SSE 事件格式**：
```
event: reasoning_step
data: {"step": 1, "type": "info", "content": "正在抽取第一份文件..."}

event: reasoning_step
data: {"step": 2, "type": "thinking", "content": "發現主題：服務範圍、付款條件、違約責任"}

event: report
data: {"markdown": "# 比較報告\n..."}

event: done
data: {}
```

---

## 決策 6：Session 管理與 PDF 清除

**決策**：
- Session ID 由後端在 POST `/api/sessions` 時生成（UUID v4），回傳給前端儲存於 `sessionStorage`
- 前端使用 `beforeunload` 事件觸發 `navigator.sendBeacon('/api/sessions/{id}', DELETE-like payload)` 或 `fetch` with `keepalive: true`
- 後端同時維護 TTL 機制：超過 30 分鐘無活動的 Session 由背景任務清除

**理由**：
- `sendBeacon` 在頁面卸載時比 `fetch` 更可靠
- TTL 作為備援確保即使 `beforeunload` 未觸發（強制關閉瀏覽器），資料仍會被清除

---

## 決策 7：Docker Compose 架構

**決策**：
```yaml
services:
  backend:   # FastAPI，port 8000
  frontend:  # React (Nginx)，port 3000 → 80
```

- 後端透過環境變數接收 `LITELLM_BASE_URL`、`LITELLM_API_KEY`、`LITELLM_MODEL`
- 前端 Nginx 配置 `/api` 反向代理至後端，避免 CORS 問題
- 無需額外 ChromaDB 容器（記憶體模式）

**所有 NEEDS CLARIFICATION 已解決**：本研究報告完整解決 Phase 0 所有技術決策，可進入 Phase 1 設計。
