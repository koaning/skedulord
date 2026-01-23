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

// Static mode is auto-detected at runtime
let staticModeDetected: boolean | null = null;
let cachedRuns: RunEntry[] | null = null;

export function isStaticMode(): boolean {
  return staticModeDetected === true;
}

function authHeaders() {
  return authHeader ? { Authorization: authHeader } : {};
}

export function setAuthHeader(username: string, password: string) {
  authHeader = `Basic ${btoa(`${username}:${password}`)}`;
}

export function clearAuthHeader() {
  authHeader = null;
}

async function detectStaticMode(): Promise<boolean> {
  if (staticModeDetected !== null) {
    return staticModeDetected;
  }

  // Try to fetch static runs.json - if it exists, we're in static mode
  try {
    const response = await fetch(`${apiBase}/api/runs.json`, { method: 'HEAD' });
    staticModeDetected = response.ok;
  } catch {
    staticModeDetected = false;
  }

  return staticModeDetected;
}

async function fetchRunsStatic(params: {
  limit?: number;
  name?: string;
  status?: string;
  date?: string;
}): Promise<RunEntry[]> {
  // Fetch all runs from static JSON if not cached
  if (!cachedRuns) {
    const response = await fetch(`${apiBase}/api/runs.json`);
    if (!response.ok) {
      throw new ApiError(response.status, "Failed to load runs");
    }
    cachedRuns = await response.json();
  }

  // Apply client-side filtering
  let runs = [...(cachedRuns || [])];

  if (params.name) {
    const searchName = params.name.toLowerCase();
    runs = runs.filter(r => r.name.toLowerCase().includes(searchName));
  }
  if (params.status) {
    runs = runs.filter(r => r.status === params.status);
  }
  if (params.date) {
    runs = runs.filter(r => r.start.includes(params.date));
  }
  if (params.limit) {
    runs = runs.slice(0, params.limit);
  }

  return runs;
}

async function fetchRunsDynamic(params: {
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

export async function fetchRuns(params: {
  limit?: number;
  name?: string;
  status?: string;
  date?: string;
}): Promise<RunEntry[]> {
  const isStatic = await detectStaticMode();
  if (isStatic) {
    return fetchRunsStatic(params);
  }
  return fetchRunsDynamic(params);
}

export async function fetchLog(runId: string): Promise<{ logpath: string; content: string }> {
  const isStatic = await detectStaticMode();

  if (isStatic) {
    const response = await fetch(`${apiBase}/api/logs/${runId}.json`);
    if (!response.ok) {
      throw new ApiError(response.status, "Failed to load log");
    }
    return response.json();
  }

  const response = await fetch(`${apiBase}/api/logs/${runId}`, {
    headers: authHeaders()
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Failed to load log");
  }
  return response.json();
}
