export interface ReasoningStep {
  step: number;
  type: "info" | "thinking" | "result";
  content: string;
}

export interface SSECallbacks {
  onReasoningStep: (step: ReasoningStep) => void;
  onReport: (markdown: string) => void;
  onDone: () => void;
  onError: (message: string) => void;
}

export function subscribeToStream(
  sessionId: string,
  jobId: string,
  callbacks: SSECallbacks
): () => void {
  const url = `/api/sessions/${sessionId}/compare/${jobId}/stream`;
  const source = new EventSource(url);

  source.addEventListener("reasoning_step", (e: MessageEvent) => {
    try {
      const step: ReasoningStep = JSON.parse(e.data);
      callbacks.onReasoningStep(step);
    } catch {
      // ignore parse errors
    }
  });

  source.addEventListener("report", (e: MessageEvent) => {
    try {
      const { markdown } = JSON.parse(e.data);
      callbacks.onReport(markdown);
    } catch {
      // ignore parse errors
    }
  });

  source.addEventListener("done", () => {
    source.close();
    callbacks.onDone();
  });

  source.addEventListener("error", (e: MessageEvent) => {
    try {
      const parsed = JSON.parse((e as MessageEvent).data || "{}");
      callbacks.onError(parsed.message || "Stream error");
    } catch {
      callbacks.onError("Stream connection error");
    }
    source.close();
  });

  return () => source.close();
}
