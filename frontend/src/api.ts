import type { Question, RunMode, SystemId } from "./types";

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail ?? `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getQuestions(): Promise<Question[]> {
  return json(await fetch("/api/questions"));
}

export async function getHealth(): Promise<Record<string, unknown>> {
  return json(await fetch("/api/health"));
}

export async function createRun(questionId: string, system: SystemId, mode: RunMode) {
  return json<{ id: string }>(
    await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, system, mode }),
    }),
  );
}

export async function cancelRun(runId: string): Promise<void> {
  await json(
    await fetch(`/api/runs/${runId}/cancel`, {
      method: "POST",
    }),
  );
}
