---
description: "大型 PDF 文件比較 Agent 任務清單"
---

# 任務清單：大型 PDF 文件比較 Agent

**輸入**：設計文件來自 `specs/001-pdf-compare-agent/`

**前置條件**：plan.md（必要）、spec.md（必要）、data-model.md、contracts/、research.md

**測試**：規格中未明確要求 TDD，本清單不包含測試任務（可於後續 Polish 階段補充）。

**組織方式**：任務依使用者故事分組，支援各故事獨立實作與驗證。

---

## 格式說明：`[ID] [P?] [Story?] 說明（含檔案路徑）`

- **[P]**：可平行執行（不同檔案，無未完成的依賴）
- **[Story]**：對應的使用者故事（US1、US2、US3）
- 每個任務包含精確的檔案路徑

---

## Phase 1：初始化（Setup）

**目的**：建立專案骨架，確保 Docker 環境可啟動

- [ ] T001 建立後端目錄結構：`backend/app/api/`、`backend/app/services/`、`backend/app/models/`、`backend/tests/`
- [ ] T002 [P] 建立前端目錄結構：`frontend/src/components/`、`frontend/src/services/`
- [ ] T003 建立 `backend/requirements.txt`（fastapi、uvicorn、pdfplumber、pymupdf、pytesseract、chromadb、litellm、python-multipart、python-dotenv、tiktoken）
- [ ] T004 [P] 建立 `frontend/package.json`（react 18、typescript、vite、react-markdown）
- [ ] T005 建立 `backend/Dockerfile`（python:3.11-slim，安裝 tesseract-ocr tesseract-ocr-chi-tra，COPY requirements.txt，pip install）
- [ ] T006 [P] 建立 `frontend/Dockerfile`（multi-stage：node:20-alpine build，nginx:alpine serve）
- [ ] T007 建立 `docker-compose.yml`（backend port 8000、frontend port 3000，共用 .env，frontend nginx 代理 /api 至 backend）
- [ ] T008 建立 `.env.example`（LITELLM_BASE_URL=https://lllm.xsong.us、LITELLM_API_KEY=、LITELLM_MODEL=claude-sonnet-4-6）
- [ ] T009 [P] 建立 `frontend/nginx.conf`（靜態檔案服務 + location /api 反向代理至 http://backend:8000）

**檢查點**：執行 `docker compose up --build`，前端可在 localhost:3000 開啟，後端 localhost:8000/docs 可存取

---

## Phase 2：基礎層（Foundational）

**目的**：Session 管理、資料模型、FastAPI 應用入口——所有使用者故事的必要前置

**⚠️ 重要**：此階段完成前，任何使用者故事均無法開始

- [ ] T010 建立 `backend/app/models/session.py`（Session dataclass：session_id、created_at、last_active_at、expires_at、upload_dir、status enum；SessionStatus enum：active/expired/cleaned）
- [ ] T011 [P] 建立 `backend/app/models/pdf_doc.py`（PDFDocument dataclass：pdf_id、session_id、filename、file_path、file_size_bytes、page_count、status、ocr_used、chunk_count、chroma_collection、uploaded_at、error_message；PDFStatus enum：uploading/processing/ready/error）
- [ ] T012 [P] 建立 `backend/app/models/comparison.py`（ComparisonJob dataclass：job_id、session_id、pdf_id_a、pdf_id_b、status、created_at、completed_at、report_markdown、error_message；ReasoningStep dataclass；ComparisonStatus enum：queued/running/done/error；StepType enum：info/thinking/result）
- [ ] T013 建立 `backend/app/services/session_manager.py`（in-memory dict 存 Session 與 PDFDocument；create_session、get_session、get_pdf、add_pdf、update_pdf_status、delete_session 函式；delete_session 刪除 /tmp/sessions/{id}/ 目錄與 ChromaDB collections）
- [ ] T014 建立 `backend/app/api/session.py`（POST /api/sessions 建立 Session 回傳 session_id；GET /api/sessions/{session_id} 查詢狀態；DELETE /api/sessions/{session_id} 呼叫 session_manager.delete_session）
- [ ] T015 建立 `backend/app/main.py`（FastAPI app，include_router session/upload/compare；startup event 啟動 TTL 清理背景任務；CORS middleware 允許 frontend origin）

**檢查點**：`curl -X POST http://localhost:8000/api/sessions` 回傳含 session_id 的 JSON

---

## Phase 3：使用者故事 1 — PDF 上傳、比較、推理串流（優先級：P1）🎯 MVP

**目標**：使用者上傳兩份 PDF，AI Agent 分析並透過 SSE 串流即時顯示推理步驟與最終報告

**獨立測試**：上傳兩份 PDF → 兩份均顯示「就緒」→ 點選比較 → 畫面出現推理訊息串流 → 顯示差異報告

### 後端：PDF 前處理管線

- [ ] T016 [P] [US1] 建立 `backend/app/services/pdf_extractor.py`（用 pdfplumber 抽取文字，失敗改 pymupdf；若抽取字元數 < 頁數×50 則設 needs_ocr=True；回傳每頁文字 list 與 page_count）
- [ ] T017 [P] [US1] 建立 `backend/app/services/ocr_service.py`（pytesseract 處理 needs_ocr=True 的頁面；語言設 chi_tra+eng；回傳與 pdf_extractor 相同格式的文字 list）
- [ ] T018 [US1] 建立 `backend/app/services/chunker.py`（依章節標題正規表示式切割段落；每段上限 4000 tokens（tiktoken cl100k_base）；超過上限以 sliding window 切割，overlap 200 tokens；回傳 list of dict {content, page_start, page_end, section_title, token_count}）
- [ ] T019 [US1] 建立 `backend/app/services/indexer.py`（chromadb.EphemeralClient；為每個 PDF 建立 collection `doc_{pdf_id}`；embed 用 chromadb 預設模型（all-MiniLM-L6-v2）；提供 index_chunks(pdf_id, chunks) 與 search(pdf_id, query, top_k=3) 函式）
- [ ] T020 [US1] 建立 `backend/app/api/upload.py`（POST /api/sessions/{session_id}/pdfs：驗證 .pdf 格式與 100MB 上限，儲存至 /tmp/sessions/{session_id}/{pdf_id}.pdf，更新 PDFDocument status=uploading，觸發 asyncio.create_task 執行前處理管線；GET /api/sessions/{session_id}/pdfs：回傳 PDF 清單與狀態；DELETE /api/sessions/{session_id}/pdfs/{pdf_id}：刪除檔案與 collection）

### 後端：Agent 比較與 SSE 串流

- [ ] T021 [US1] 建立 `backend/app/services/agent.py`（三步驟 async orchestrator；step1 topic_discovery：傳送兩份文件各前 5 頁給 LiteLLM claude-sonnet-4-6 產生 JSON 主題列表；step2 per_topic_compare：對每個主題用 indexer.search 各取 top-3 chunks，呼叫 LLM 比較輸出 {相同點, 差異點, 風險提示}；step3 aggregate：彙整所有主題結果產生 Markdown 報告；每步驟透過 async generator yield ReasoningStep 供 SSE 使用；LITELLM_BASE_URL、LITELLM_API_KEY 從 os.environ 讀取）
- [ ] T022 [US1] 建立 `backend/app/api/compare.py`（POST /api/sessions/{session_id}/compare：驗證兩個 pdf_id 不同且均為 ready，建立 ComparisonJob，觸發 asyncio.create_task 執行 agent；GET /api/sessions/{session_id}/compare/{job_id}/stream：StreamingResponse text/event-stream，從 async generator 讀取 ReasoningStep 逐步 yield SSE 格式；GET /api/sessions/{session_id}/compare/{job_id}：查詢任務狀態與最終報告）

### 前端：UI 元件

- [ ] T023 [P] [US1] 建立 `frontend/src/services/api.ts`（createSession()、uploadPDF(sessionId, file)、listPDFs(sessionId)、startComparison(sessionId, pdfIdA, pdfIdB)、getJob(sessionId, jobId)）
- [ ] T024 [P] [US1] 建立 `frontend/src/services/sse.ts`（subscribeToStream(sessionId, jobId, callbacks) 用 EventSource；callbacks: {onReasoningStep, onReport, onDone, onError}；回傳 close() 函式）
- [ ] T025 [P] [US1] 建立 `frontend/src/components/PDFUpload.tsx`（拖放區域 + 點選上傳按鈕；呼叫 api.uploadPDF；上傳後顯示 filename 與 status；每 2 秒輪詢 listPDFs 直到 status=ready）
- [ ] T026 [P] [US1] 建立 `frontend/src/components/ReasoningStream.tsx`（接收 ReasoningStep[]；info 灰色小字、thinking 藍色等寬字型、result 綠色標記；逐步 append 不清空）
- [ ] T027 [P] [US1] 建立 `frontend/src/components/ComparisonReport.tsx`（接收 markdown string；用 react-markdown 渲染；顯示於 ReasoningStream 下方）
- [ ] T028 [US1] 建立 `frontend/src/App.tsx`（mount 時呼叫 createSession 儲存 sessionId 至 sessionStorage；渲染 PDFUpload、PDFList（US2 建立）、「開始比較」按鈕、ReasoningStream、ComparisonReport；點選比較按鈕呼叫 startComparison 再 subscribeToStream）

**檢查點（US1 完整驗證）**：依 quickstart.md 情境 1 執行，確認：推理訊息 5 秒內出現、最終報告包含三個區塊

---

## Phase 4：使用者故事 2 — 重複選取不同 PDF 組合（優先級：P2）

**目標**：使用者可在同一 Session 中多次選取不同兩份 PDF 進行比較，無需重新上傳

**獨立測試**：上傳 3 份 PDF → 選 A+B 比較完成 → 改選 A+C → 系統正確執行第二次分析，舊報告清空

### 實作

- [ ] T029 [P] [US2] 建立 `frontend/src/components/PDFList.tsx`（顯示所有已上傳的 ready PDF；每個 PDF 一個 checkbox；只允許勾選 2 份；超過 2 份時禁用其他 checkbox；顯示 filename、page_count、ocr_used、狀態指示器）
- [ ] T030 [US2] 更新 `frontend/src/App.tsx`（整合 PDFList；追蹤 selectedPdfIds state；「開始比較」按鈕：清空舊的 reasoningSteps 和 report state，關閉舊的 SSE 連線，以新選定的兩份 PDF 發起新比較）

**檢查點（US2 驗證）**：依 quickstart.md 情境 2 執行，確認第二次比較使用正確文件且舊報告被清空

---

## Phase 5：使用者故事 3 — 關閉頁面自動清除 PDF（優先級：P3）

**目標**：關閉瀏覽器分頁後，伺服器端 PDF 檔案與 ChromaDB 索引在 30 秒內清除

**獨立測試**：上傳 PDF → 關閉分頁 → 5 秒後確認 DELETE /api/sessions/{id} 已呼叫，/tmp/sessions/{id}/ 目錄不存在

### 實作

- [ ] T031 [US3] 在 `frontend/src/App.tsx` 增加 beforeunload 事件處理（window.addEventListener('beforeunload') 觸發 navigator.sendBeacon('/api/sessions/{sessionId}', '') 或 fetch(url, {method:'DELETE', keepalive:true})；unmount 時也清理）
- [ ] T032 [US3] 在 `backend/app/services/session_manager.py` 增加 TTL 清理背景任務（asyncio 每 60 秒掃描 sessions dict；expires_at < now 的 session 呼叫 delete_session；作為 app startup event 啟動的 asyncio.create_task）

**檢查點（US3 驗證）**：依 quickstart.md 情境 3 執行，確認 API 回傳 404 且 /tmp/sessions/{id}/ 已刪除

---

## Phase 6：收尾與橫切關注點（Polish）

**目的**：確保整體穩定性，完成端對端驗證

- [ ] T033 [P] 在 `backend/app/services/agent.py` 增加 LLM 呼叫錯誤處理（litellm.exceptions 捕獲，yield 錯誤 ReasoningStep，設 ComparisonJob status=error）
- [ ] T034 [P] 在 `backend/app/api/compare.py` SSE 串流增加錯誤事件 emit（捕獲 exception，yield `event: error\ndata: {...}\n\n`，確保前端 error handler 觸發）
- [ ] T035 [P] 在 `frontend/src/App.tsx` 增加錯誤狀態顯示（SSE error 事件顯示紅色錯誤訊息；上傳失敗顯示於 PDFUpload；比較失敗顯示重試按鈕）
- [ ] T036 在 `backend/app/main.py` 增加 startup 自我檢查（測試 /tmp 寫入權限、檢查 LITELLM_BASE_URL 環境變數存在）
- [ ] T037 依 `specs/001-pdf-compare-agent/quickstart.md` 執行全部 4 個驗證情境，確認端對端流程正確

---

## 依賴關係與執行順序

### Phase 依賴

- **Phase 1（初始化）**：無依賴，立即開始
- **Phase 2（基礎層）**：依賴 Phase 1 完成——阻擋所有使用者故事
- **Phase 3（US1）**：依賴 Phase 2 完成——MVP 核心
- **Phase 4（US2）**：依賴 Phase 3 完成（需要 PDFUpload 與 App.tsx 存在）
- **Phase 5（US3）**：依賴 Phase 2 完成（僅需 session_manager.py），可與 Phase 4 平行
- **Phase 6（收尾）**：依賴 Phase 3、4、5 完成

### 使用者故事依賴

- **US1（P1）**：Phase 2 後立即開始，無故事間依賴
- **US2（P2）**：依賴 US1 完成（PDFUpload + App.tsx 骨架已存在）
- **US3（P3）**：僅依賴 Phase 2（session_manager.py），可與 US1 平行

### 各故事內部順序

```
US1 後端：T016(pdf_extractor) + T017(ocr_service) [平行]
        → T018(chunker) → T019(indexer)
        → T020(upload API) → T021(agent) → T022(compare API)

US1 前端：T023(api.ts) + T024(sse.ts) + T025(PDFUpload) + T026(ReasoningStream)
        + T027(ComparisonReport) [全部平行]
        → T028(App.tsx 整合，依賴上述全部完成)
```

---

## 平行執行範例

### Phase 1 可平行執行

```bash
Task: "建立後端目錄結構（T001）"
Task: "建立前端目錄結構（T002）"  ← [P]
Task: "建立 backend/requirements.txt（T003）"
Task: "建立 frontend/package.json（T004）"  ← [P]
Task: "建立 backend/Dockerfile（T005）"
Task: "建立 frontend/Dockerfile（T006）"  ← [P]
Task: "建立 frontend/nginx.conf（T009）"  ← [P]
```

### Phase 3 後端前處理可平行執行

```bash
Task: "建立 pdf_extractor.py（T016）"  ← [P]
Task: "建立 ocr_service.py（T017）"  ← [P]
# 等兩者完成後：
Task: "建立 chunker.py（T018）"
Task: "建立 indexer.py（T019）"
```

### Phase 3 前端元件可全部平行執行

```bash
Task: "建立 api.ts（T023）"   ← [P]
Task: "建立 sse.ts（T024）"   ← [P]
Task: "建立 PDFUpload.tsx（T025）"   ← [P]
Task: "建立 ReasoningStream.tsx（T026）"   ← [P]
Task: "建立 ComparisonReport.tsx（T027）"  ← [P]
# 等全部完成後：
Task: "建立 App.tsx（T028）"
```

---

## 實作策略

### MVP 優先（僅 US1）

1. 完成 Phase 1：初始化
2. 完成 Phase 2：基礎層（CRITICAL，阻擋所有故事）
3. 完成 Phase 3：US1
4. **停下驗證**：依 quickstart.md 情境 1 測試
5. 若面試展示只需 US1，此時即可 demo

### 增量交付

1. Phase 1 + 2 完成 → 基礎就緒
2. Phase 3（US1）完成 → MVP demo 可用
3. Phase 4（US2）完成 → 多次比較功能
4. Phase 5（US3）完成 → 自動清理功能
5. Phase 6 → 穩定收尾

---

## 備註

- [P] 任務 = 不同檔案，無未完成的依賴，可平行執行
- [US?] 標籤對應 spec.md 的使用者故事
- 每個故事完成後以 quickstart.md 對應情境驗證
- `navigator.sendBeacon` 的 HTTP method 僅支援 POST；需後端提供 POST /api/sessions/{id}/cleanup 或用 fetch with keepalive
- ChromaDB EphemeralClient 在程序重啟後資料遺失，屬預期行為（MVP 可接受）
- pytesseract Dockerfile 需安裝 `tesseract-ocr-chi-tra` 繁中語言包
