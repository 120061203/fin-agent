兩份大型 PDF 文件比較 AI Agent

### 情境：年報財務分析對比

---

### 核心挑戰

大型 PDF 無法塞進單次 Context Window（可能 200+ 頁），需要**分段處理 + 結構化彙整**。

---

### 系統架構圖

```
[輸入]
PDF_A  PDF_B
  │      │
  ▼      ▼
┌──────────────────────────────────────┐
│          PDF Processing Pipeline      │
│  1. 文字抽取（pdfplumber / pymupdf）  │
│  2. 章節/段落結構識別                 │
│  3. 分段 Chunking（by section）       │
└──────────────────────────────────────┘
  │                    │
  ▼                    ▼
[Doc A Index]      [Doc B Index]
(ChromaDB)         (ChromaDB)
  │                    │
  └────────┬───────────┘
           ▼
┌──────────────────────────────────┐
│       Comparison Orchestrator     │
│                                   │
│  Step 1: Topic Discovery          │
│    → 從兩份文件各抽主題列表       │
│                                   │
│  Step 2: Per-Topic Comparison     │
│    → 對每個主題做向量搜尋         │
│    → 各取 Top-K Context           │
│    → 呼叫 compare_topic() Tool    │
│                                   │
│  Step 3: Summary Aggregation      │
│    → 彙整所有主題的比較結果       │
│    → 生成結構化差異報告           │
└──────────────────────────────────┘
           │
           ▼
    ┌─────────────┐
    │ 輸出報告     │
    │ Markdown /  │
    │ JSON        │
    └─────────────┘
```

---

### 元件說明

| 元件 | 技術選型 | 說明 |
|------|---------|------|
| PDF 解析 | pdfplumber / pymupdf | 抽取文字，保留頁碼資訊 |
| 章節識別 | 正則 + LLM 輔助 | 識別標題層級，結構化切割 |
| Vector DB | ChromaDB（兩個獨立 Collection） | A / B 分開索引，互不干擾 |
| 比較 Agent | LangGraph / 自訂 ReAct | 控制多步驟比較流程 |
| 輸出格式 | Structured Output（JSON Schema） | 確保差異報告格式一致 |

---

### 資料流

```
[文件處理]
PDF_A → 抽取 → 章節切割 → 存入 Collection_A
PDF_B → 抽取 → 章節切割 → 存入 Collection_B

[比較流程]
① Topic Discovery：
   LLM 讀取兩份文件的目錄/前幾頁 → 生成比較主題列表
   例：["第一條：服務範圍", "第三條：付款條件", "違約責任" ...]

② Per-Topic Loop（可平行化）：
   For each topic:
     search_doc_a(topic) → Context_A
     search_doc_b(topic) → Context_B
     compare(Context_A, Context_B) → {相同點, 差異點, 風險提示}

③ Aggregation：
   彙整所有 topic 的結果 → 生成最終 Markdown 報告
```

---

### 目錄結構

```
project/
├── pdfs/
│   ├── doc_a.pdf
│   └── doc_b.pdf
├── src/
│   ├── pdf_parser.py       # PDF 抽取與章節識別
│   ├── indexer.py          # 建立兩份文件的向量索引
│   ├── comparator.py       # Per-topic 比較邏輯
│   ├── orchestrator.py     # 主控流程（Topic Discovery → Loop → Summary）
│   └── reporter.py         # 輸出 Markdown 報告
├── main.py
└── requirements.txt
```

---

### 難點與對策

| 難點 | 對策 |
|------|------|
| PDF 格式不統一（掃描版、表格、浮水印） | pdfplumber 優先，失敗則 OCR（pytesseract）兜底 |
| 兩份文件章節不對齊 | Topic Discovery 由 LLM 自動發現對應關係，而非硬對齊頁碼 |
| 比較結果過長 | 每個 Topic 獨立比較，最後再 Summarize，避免單次 Prompt 過大 |
| 平行比較效率 | asyncio + 並發呼叫 LLM API，加速 Per-Topic 比較 |

---
