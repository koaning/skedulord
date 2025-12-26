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

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const apiBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
let authHeader: string | null = null;

function authHeaders() {
  return authHeader ? { Authorization: authHeader } : {};
}

export function setAuthHeader(username: string, password: string) {
  authHeader = `Basic ${btoa(`${username}:${password}`)}`;
}

export function clearAuthHeader() {
  authHeader = null;
}

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
  const response = await fetch(`${apiBase}/api/runs?${query.toString()}`, {
    headers: authHeaders()
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Failed to load runs");
  }
  return response.json();
}

export async function fetchLog(runId: string): Promise<{ logpath: string; content: string }> {
  const response = await fetch(`${apiBase}/api/logs/${runId}`, {
    headers: authHeaders()
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Failed to load log");
  }
  return response.json();
}
