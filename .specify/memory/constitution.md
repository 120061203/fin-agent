<!--
Sync Impact Report
==================
Version Change: (未版本化範本) → 1.0.0
Modified Principles: 全部為新增（從範本佔位符填入）
Added Sections:
  - 核心原則（5 條）
  - 技術堆疊約束
  - 開發工作流程
  - Governance
Removed Sections: 無（首次填寫）
Templates Requiring Updates:
  - .specify/templates/plan-template.md  ✅ 內容與原則相容，無需修改
  - .specify/templates/spec-template.md  ✅ 內容與原則相容，無需修改
  - .specify/templates/tasks-template.md ✅ 內容與原則相容，無需修改
Follow-up TODOs:
  - RATIFICATION_DATE: 以今日 2026-07-02 作為批准日（專案首次建立）
-->

# 大型 PDF 財務文件比較 Agent 專案憲章

## 核心原則

### 一、MVP 優先（NON-NEGOTIABLE）

每個功能實作 MUST 以最小可行產品為目標，不得引入超出當前需求的複雜度。
YAGNI（You Aren't Gonna Need It）原則嚴格執行：
- 禁止為假設性未來需求設計抽象層或框架
- 禁止引入未被現有使用案例驅動的設計模式
- 三行類似程式碼優於一個過早的抽象封裝
- 每次提交 MUST 交付可獨立驗證的可運行功能

**理由**：財務分析場景需求變動快，過早的架構決策往往成為技術債。

### 二、大型 PDF 前處理管線（NON-NEGOTIABLE）

大型 PDF 文件（200+ 頁）MUST 透過資料前處理萃取後再送入 LLM，嚴禁直接將原始 PDF 塞入 LLM Context Window：
- 前處理流程 MUST 包含：文字抽取 → 章節/段落結構識別 → 分段 Chunking
- 掃描版 PDF MUST 先透過 OCR 轉換為可搜尋文字，再進行後續處理
- 每次送入 LLM 的 Context MUST 為經結構化萃取的摘要或分段內容，不得為整份文件原文
- 前處理模組 MUST 獨立可測試，與 LLM 呼叫解耦

**理由**：LLM Context Window 有限，直接塞入大型 PDF 會導致截斷或幻覺；前處理萃取確保資訊品質與可靠性。

### 三、FastAPI + Dockerfile 部署標準

專案 MUST 以 FastAPI 作為唯一 REST API 框架，並提供 Dockerfile 進行容器化部署：
- API 端點 MUST 遵循 RESTful 設計規範
- Dockerfile MUST 可於本機 `docker build && docker run` 即可啟動服務，無需額外手動配置
- 環境變數（API Key、模型名稱等）MUST 透過 `.env` 或環境變數注入，不得硬編碼
- 不得引入 Kubernetes、服務網格等超出 MVP 範疇的部署複雜度

**理由**：Dockerfile 確保環境一致性；FastAPI 提供自動 API 文件與高效能非同步支援。

### 四、OCR 支援掃描版 PDF

系統 MUST 支援掃描版（非純文字）PDF 的處理：
- 前處理管線 MUST 優先使用 pdfplumber / pymupdf 進行文字抽取
- 當文字抽取結果為空或品質不足時，MUST 自動退回 OCR（pytesseract 或同等方案）
- OCR 模組 MUST 可獨立測試，並能處理常見財務報告格式（表格、浮水印、多欄版面）

**理由**：台灣財務年報常以掃描 PDF 形式存在；缺乏 OCR 支援將導致核心功能無法使用。

### 五、LiteLLM + Claude Sonnet 4.6 模型整合

所有 LLM 呼叫 MUST 透過 LiteLLM 統一代理，預設模型為 `claude-sonnet-4-6`：
- 模型名稱 MUST 透過環境變數設定（`LITELLM_MODEL`），不得硬編碼
- LLM 呼叫 MUST 包含結構化輸出（Structured Output）以確保回應格式一致
- 每次 LLM 呼叫 MUST 記錄 token 用量與回應時間，便於成本追蹤
- 禁止在單次 LLM 呼叫中傳入超過 50,000 tokens 的 context（強制前處理原則）

**理由**：LiteLLM 提供統一介面，便於日後切換模型；Sonnet 4.6 在財務分析任務上具備優秀的繁中理解能力。

## 技術堆疊約束

本專案 MUST 使用以下技術堆疊，不得在未記錄理由的情況下替換核心元件：

| 層次 | 技術選型 | 說明 |
|------|---------|------|
| API 框架 | FastAPI | REST API + 自動文件 |
| 容器化 | Docker / Dockerfile | 本機與雲端一致部署 |
| PDF 文字抽取 | pdfplumber / pymupdf | 主要抽取工具 |
| OCR 備援 | pytesseract | 掃描版 PDF 退回處理 |
| LLM 代理 | LiteLLM | 統一模型介面 |
| 預設 LLM 模型 | claude-sonnet-4-6 | 財務繁中分析主力模型 |
| 向量資料庫 | ChromaDB | 文件分段索引（MVP 階段） |
| 語言 | Python 3.11+ | 主開發語言 |

引入上表以外的新依賴 MUST 在 PR 說明中提供：(a) 解決的具體問題、(b) 評估過的替代方案、(c) 無法使用現有依賴的原因。

## 開發工作流程

本專案採用以下工作流程，確保 MVP 導向的增量交付：

1. **功能規格先行**：每個功能 MUST 先撰寫 spec.md（使用者情境 + 驗收條件），再開始實作
2. **前處理與 LLM 解耦**：前處理模組（PDF 抽取、OCR、Chunking）MUST 可獨立執行與測試，不依賴 LLM 服務
3. **API 優先**：功能 MUST 先以 FastAPI 端點暴露，確保可透過 HTTP 呼叫驗證
4. **Docker 本機驗證**：每個功能完成後，MUST 於 Docker 容器環境中執行基本 smoke test
5. **繁體中文文件**：所有 spec、plan、tasks 文件 MUST 以繁體中文撰寫，程式碼註解可使用英文

禁止事項：
- 禁止在未通過本機 Docker 測試前提交 PR
- 禁止引入需要額外基礎設施（資料庫遷移工具、訊息佇列等）的依賴，除非 spec 明確要求
- 禁止跳過 PDF 前處理步驟直接呼叫 LLM

## Governance

本憲章為專案最高技術治理文件，優先於所有其他慣例與偏好設定。

**修訂程序**：
- MAJOR 版本（移除或重新定義原則）：MUST 由專案負責人審核，並提供遷移計畫
- MINOR 版本（新增原則或章節）：MUST 記錄修訂理由
- PATCH 版本（文字澄清、錯字修正）：可直接提交，無需額外審核

**合規審查**：
- 每次 PR 審查 MUST 確認變更符合憲章原則，特別是「MVP 優先」與「前處理管線」兩條 NON-NEGOTIABLE 原則
- 違反憲章的複雜度 MUST 在 plan.md 的「複雜度追蹤」表格中明確記錄並提供理由

**版本策略**：遵循 Semantic Versioning（語意化版本）。

---

**版本**：1.0.0 | **批准日期**：2026-07-02 | **最後修訂**：2026-07-02
