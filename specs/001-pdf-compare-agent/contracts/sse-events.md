# SSE 事件合約：推理過程串流

**端點**：`GET /api/sessions/{session_id}/compare/{job_id}/stream`

前端使用 `EventSource` API 訂閱此端點，接收以下事件。

---

## 事件格式總覽

```
event: {event_type}
data: {JSON payload}

```

> 注意：每個事件後跟兩個換行（`\n\n`），符合 SSE 規範。

---

## 事件類型

### `reasoning_step`

AI 推理過程步驟，用於在前端即時顯示分析進度。

**payload**：
```json
{
  "step": 1,
  "type": "info",
  "content": "正在讀取第一份文件（annual_report_2024.pdf）前處理結果..."
}
```

```json
{
  "step": 2,
  "type": "info",
  "content": "正在讀取第二份文件（annual_report_2023.pdf）前處理結果..."
}
```

```json
{
  "step": 3,
  "type": "thinking",
  "content": "已識別以下比較主題：\n1. 服務範圍\n2. 付款條件\n3. 違約責任\n4. 智慧財產權\n5. 爭議解決機制"
}
```

```json
{
  "step": 4,
  "type": "thinking",
  "content": "正在比較主題：服務範圍（第 1/5 個主題）"
}
```

```json
{
  "step": 5,
  "type": "result",
  "content": "【服務範圍】比較完成：發現 2 項相同點、3 項差異點、1 項風險提示"
}
```

**`type` 枚舉值說明**：

| 值 | 顯示樣式建議 | 語意 |
|----|-------------|------|
| `info` | 灰色文字，小字 | 系統狀態訊息 |
| `thinking` | 藍色背景，等寬字型 | AI 推理過程 |
| `result` | 綠色標記 | 單一主題完成 |

---

### `report`

分析全部完成，回傳最終差異報告。

**payload**：
```json
{
  "markdown": "# 比較報告\n\n## 執行摘要\n兩份年報在服務範圍上基本一致，但付款條件有顯著差異...\n\n## 詳細比較\n\n### 服務範圍\n**相同點**：...\n**差異點**：...\n**風險提示**：..."
}
```

---

### `done`

串流結束信號，前端收到後關閉 `EventSource` 連線。

**payload**：
```json
{}
```

---

### `error`

分析過程發生錯誤。

**payload**：
```json
{
  "message": "LLM API 呼叫失敗：連線逾時，請稍後重試",
  "step": 4
}
```

---

## 前端消費範例

```typescript
const source = new EventSource(`/api/sessions/${sessionId}/compare/${jobId}/stream`);

source.addEventListener('reasoning_step', (e) => {
  const step = JSON.parse(e.data);
  appendReasoningStep(step); // 顯示於推理串流區
});

source.addEventListener('report', (e) => {
  const { markdown } = JSON.parse(e.data);
  renderReport(markdown); // 渲染最終報告
});

source.addEventListener('done', () => {
  source.close();
});

source.addEventListener('error', (e) => {
  const { message } = JSON.parse(e.data);
  showError(message);
  source.close();
});
```
