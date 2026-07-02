# 實作計畫：大型 PDF 文件比較 Agent

**分支**：`001-pdf-compare-agent` | **日期**：2026-07-02 | **規格**：[spec.md](./spec.md)

**輸入**：功能規格來自 `specs/001-pdf-compare-agent/spec.md`

---

## 摘要

本專案為技術面試展示用系統，允許使用者上傳兩份大型 PDF（含掃描版），透過 AI Agent 進行主題式比較分析，並將推理過程即時串流至 React 前端。關鍵技術決策：大型 PDF 必須先經過前處理管線（抽取 → 章節識別 → Chunking → ChromaDB 索引）後才送入 LLM，避免 Context Window 溢出。

---

## 技術背景

**語言/版本**：Python 3.11（後端）、Node.js 20 / TypeScript（前端）

**主要依賴**：
- 後端：FastAPI、pdfplumber、pymupdf、pytesseract、chromadb、litellm、python-multipart
- 前端：React 18、TypeScript、Vite

**儲存**：本機檔案系統（暫存 PDF，session 結束後刪除）＋ ChromaDB（記憶體模式，session 結束後清除）

**測試**：pytest（後端）、手動 smoke test via Docker Compose

**目標平台**：Linux 容器（Docker Compose），本機開發環境

**專案類型**：全端 Web 服務（後端 API + 前端 SPA）

**效能目標**：
- 使用者點選分析後，5 秒內出現第一則推理訊息
- 單份 100 頁 PDF 前處理時間不超過 60 秒

**約束**：
- 每次 LLM 呼叫 Context 上限 50,000 tokens（依憲章規定）
- 每段 Chunk 上限 4,000 tokens
- MVP 僅支援單一使用者操作，不需橫向擴展

**規模/範圍**：單使用者，每次工作階段最多 10 份 PDF，MVP 功能

---

## 憲章檢查

*GATE：必須在 Phase 0 研究前通過。Phase 1 設計後重新檢查。*

| 原則 | 狀態 | 說明 |
|------|------|------|
| 一、MVP 優先 | ✅ 通過 | 不引入 K8s、訊息佇列、資料庫遷移工具；ChromaDB 以記憶體模式運行 |
| 二、大型 PDF 前處理管線 | ✅ 通過 | 明確設計：抽取 → 章節識別 → Chunking → 向量索引，不直接送原始 PDF 入 LLM |
| 三、FastAPI + Dockerfile | ✅ 通過 | 後端用 FastAPI，提供 `backend/Dockerfile`、`frontend/Dockerfile`、`docker-compose.yml` |
| 四、OCR 支援 | ✅ 通過 | pdfplumber 優先，文字量不足時自動退回 pytesseract |
| 五、LiteLLM + claude-sonnet-4-6 | ✅ 通過 | 透過 LiteLLM SDK 呼叫 `https://lllm.xsong.us`，模型設為 `claude-sonnet-4-6` |

**Phase 1 後重新檢查**：✅ 設計未違反任何原則，無需記錄例外。

---

## 專案結構

### 文件（本功能）

```text
specs/001-pdf-compare-agent/
├── plan.md              # 本檔案
├── research.md          # Phase 0 研究輸出
├── data-model.md        # Phase 1 資料模型
├── quickstart.md        # Phase 1 驗證指南
├── contracts/           # Phase 1 API 合約
│   ├── session-api.md
│   ├── pdf-api.md
│   ├── compare-api.md
│   └── sse-events.md
└── tasks.md             # Phase 2 輸出（/speckit-tasks 產生）
```

### 原始碼（儲存庫根目錄）

```text
backend/
├── app/
│   ├── main.py                  # FastAPI 應用入口
│   ├── api/
│   │   ├── session.py           # 工作階段建立/刪除
│   │   ├── upload.py            # PDF 上傳
│   │   └── compare.py           # 分析觸發 + SSE 串流
│   ├── services/
│   │   ├── pdf_extractor.py     # pdfplumber/pymupdf 文字抽取
│   │   ├── ocr_service.py       # pytesseract OCR 備援
│   │   ├── chunker.py           # 章節識別與分段
│   │   ├── indexer.py           # ChromaDB 向量索引
│   │   ├── agent.py             # LiteLLM Agent 比較邏輯
│   │   └── session_manager.py   # Session 清理（TTL + 手動）
│   └── models/
│       ├── session.py
│       ├── pdf_doc.py
│       └── comparison.py
├── tests/
│   └── test_pipeline.py
├── Dockerfile
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   │   ├── PDFUpload.tsx         # 拖放/點選上傳
│   │   ├── PDFList.tsx           # 已上傳文件清單＋選取
│   │   ├── ReasoningStream.tsx   # 推理步驟即時串流顯示
│   │   └── ComparisonReport.tsx  # 最終差異報告渲染
│   ├── services/
│   │   ├── api.ts                # REST API 呼叫
│   │   └── sse.ts                # SSE 事件訂閱
│   └── App.tsx
├── Dockerfile
├── nginx.conf
└── package.json

docker-compose.yml
```

**結構決策**：採用 Option 2（前後端分離），後端為 FastAPI Python 服務，前端為 React SPA 透過 Nginx 提供靜態檔案。兩個容器透過 Docker Compose 串接，環境變數由 `.env` 注入。

---

## 複雜度追蹤

> 本次設計無憲章違規，此區段不適用。
