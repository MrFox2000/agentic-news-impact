import type { RunHandlers, StreamEvent } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
    return response.statusText || `Request failed with ${response.status}`;
  } catch {
    return response.statusText || `Request failed with ${response.status}`;
  }
}

/**
 * Starts an analysis and consumes the agent's event stream.
 * `fetch` is used rather than `EventSource` because the request carries a body.
 */
export async function runAnalysis(
  symbol: string,
  question: string,
  days: number | null,
  handlers: RunHandlers,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, question, days }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (!response.body) {
    throw new Error("This browser cannot read streamed responses.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.split("\n").find((part) => part.startsWith("data: "));
      if (!line) continue;

      const event = JSON.parse(line.slice(6)) as StreamEvent;
      if (event.type === "step") handlers.onStep({ node: event.node, detail: event.detail });
      else if (event.type === "report") handlers.onReport(event.markdown);
      else if (event.type === "error") handlers.onError(event.message);
    }
  }
}
