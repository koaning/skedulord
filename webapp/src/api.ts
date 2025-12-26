export type RunStatus = "success" | "fail" | string;

export interface RunEntry {
  id: string;
  name: string;
  command: string;
  status: RunStatus;
  start: string;
  end: string;
  logpath: string;
}

const apiBase = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export async function fetchRuns(params: {
  limit?: number;
  name?: string;
  status?: string;
  date?: string;
}): Promise<RunEntry[]> {
  const query = new URLSearchParams();
  if (params.limit) query.set("limit", String(params.limit));
  if (params.name) query.set("name", params.name);
  if (params.status) query.set("status", params.status);
  if (params.date) query.set("date", params.date);
  const response = await fetch(`${apiBase}/api/runs?${query.toString()}`);
  if (!response.ok) {
    throw new Error("Failed to load runs");
  }
  return response.json();
}

export async function fetchLog(runId: string): Promise<{ logpath: string; content: string }> {
  const response = await fetch(`${apiBase}/api/logs/${runId}`);
  if (!response.ok) {
    throw new Error("Failed to load log");
  }
  return response.json();
}
