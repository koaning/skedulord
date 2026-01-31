import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import {
  AlertCircle,
  Check,
  Command,
  Copy,
  CornerUpLeft,
  Filter,
  LogOut,
  Search,
  Moon,
  RefreshCw,
  Sun
} from "lucide-react";

import {
  ApiError,
  clearAuthHeader,
  detectNoAuthMode,
  fetchLog,
  fetchRuns,
  isNoAuthMode,
  isStaticMode,
  setAuthHeader,
  type RunEntry
} from "./api";

const MAX_RECENT_RUNS = 20;
const RUNS_PER_PAGE = 25;
const AUTH_STORAGE_KEY = "skedulord_basic_auth";

function statusColor(status: string, attempt: number = 1) {
  if (status === "success" && attempt > 1) return "bg-amber-400";
  if (status === "success") return "bg-emerald-500";
  if (status === "fail") return "bg-rose-500";
  return "bg-amber-400";
}

function StatusPill({ status, attempt = 1 }: { status: string; attempt?: number }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-ink shadow-sm dark:bg-slate-900/70 dark:text-slate-100">
      <span className={`h-2 w-2 rounded-full ${statusColor(status, attempt)}`} />
      {status}{attempt > 1 ? ` (${attempt} attempts)` : ""}
    </span>
  );
}

function getDurationMs(run: RunEntry) {
  const start = Date.parse(run.start);
  const end = Date.parse(run.end);
  if (!Number.isFinite(start) || !Number.isFinite(end)) return 0;
  return Math.max(0, end - start);
}

function formatDuration(ms: number) {
  if (!ms) return "0s";
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round(minutes / 60);
  return `${hours}h`;
}

function filenameOnly(path?: string | null) {
  if (!path) return "";
  const normalized = path.replace(/\\/g, "/");
  const parts = normalized.split("/");
  return parts[parts.length - 1] || "";
}

function RunBars({
  runs,
  variant = "default",
  onSelectRun,
  onHoverRun,
  highlightRunId
}: {
  runs: RunEntry[];
  variant?: "default" | "compact";
  onSelectRun?: (run: RunEntry) => void;
  onHoverRun?: (run: RunEntry | null) => void;
  highlightRunId?: string | null;
}) {
  const recentRuns = runs.slice(0, MAX_RECENT_RUNS);
  const durations = recentRuns.map((run) => getDurationMs(run));
  const maxDuration = Math.max(0, ...durations);
  const isCompact = variant === "compact";
  const maxHeight = isCompact ? 40 : 52;
  const minHeight = isCompact ? 8 : 10;
  const barWidth = isCompact ? "w-2.5" : "w-3";
  const barGap = isCompact ? "gap-1.5" : "gap-2";
  const interactive = Boolean(onSelectRun);

  return (
    <div
      className={`flex items-end ${barGap}`}
      aria-label="Recent runs"
      role="list"
      onMouseLeave={() => {
        if (onHoverRun) onHoverRun(null);
      }}
    >
      {recentRuns.map((run, index) => {
        const duration = durations[index];
        const height = maxDuration
          ? Math.max(minHeight, Math.round((duration / maxDuration) * maxHeight))
          : minHeight;
        const label = `Run ${run.id.slice(0, 8)} · ${formatDuration(duration)} · ${run.status}${run.attempt > 1 ? ` (${run.attempt} attempts)` : ""}`;
        const isHighlighted = highlightRunId === run.id;

        return (
          <button
            key={run.id}
            type="button"
            className={`group relative ${barWidth} rounded-full ${statusColor(
              run.status,
              run.attempt
            )} transition-transform ${interactive ? "cursor-pointer" : "cursor-default"} hover:-translate-y-0.5 hover:shadow-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink ${
              isHighlighted
                ? "ring-2 ring-ink/40 ring-offset-2 ring-offset-white/80 dark:ring-white/40 dark:ring-offset-slate-900/70"
                : ""
            }`}
            style={{ height }}
            aria-label={label}
            title={label}
            role="listitem"
            onClick={(event) => {
              if (!onSelectRun) return;
              event.stopPropagation();
              onSelectRun(run);
            }}
            onMouseEnter={() => {
              if (onHoverRun) onHoverRun(run);
            }}
          >
          </button>
        );
      })}
    </div>
  );
}

function LoginScreen({
  theme,
  onToggleTheme,
  onSubmit,
  error,
  busy,
  username,
  password,
  onUsernameChange,
  onPasswordChange
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  error: string | null;
  busy: boolean;
  username: string;
  password: string;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
}) {
  const isDark = theme === "dark";
  return (
    <div className="app-shell">
      <div className="mx-auto flex min-h-screen max-w-xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-plum dark:text-orange-300">Skedulord</p>
            <h1 className="mt-2 text-3xl font-semibold text-ink dark:text-slate-100">Sign in</h1>
          </div>
          <button
            onClick={onToggleTheme}
            className="inline-flex h-9 items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 text-xs font-semibold text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
            type="button"
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            {isDark ? "Light" : "Dark"}
          </button>
        </header>

        <section className="rounded-3xl border border-ink/10 bg-white/80 p-8 shadow-card dark:border-white/10 dark:bg-slate-900/70">
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label className="flex flex-col gap-2 text-sm font-semibold text-ink dark:text-slate-100">
              Username
              <input
                value={username}
                onChange={(event) => onUsernameChange(event.target.value)}
                type="text"
                name="username"
                autoComplete="username"
                autoFocus
                className="h-11 rounded-2xl border border-ink/10 bg-white/90 px-4 text-sm font-normal text-ink shadow-sm focus:border-ink/40 focus:outline-none focus:ring-2 focus:ring-ink/10 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100 dark:focus:border-white/40 dark:focus:ring-white/10"
                required
              />
            </label>
            <label className="flex flex-col gap-2 text-sm font-semibold text-ink dark:text-slate-100">
              Password
              <input
                value={password}
                onChange={(event) => onPasswordChange(event.target.value)}
                type="password"
                name="password"
                autoComplete="current-password"
                className="h-11 rounded-2xl border border-ink/10 bg-white/90 px-4 text-sm font-normal text-ink shadow-sm focus:border-ink/40 focus:outline-none focus:ring-2 focus:ring-ink/10 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100 dark:focus:border-white/40 dark:focus:ring-white/10"
                required
              />
            </label>
            {error ? (
              <div className="flex items-center gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            ) : null}
            <button
              type="submit"
              disabled={busy}
              className="mt-2 inline-flex h-11 items-center justify-center gap-2 rounded-2xl bg-ink px-4 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 hover:shadow-card disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-ink"
            >
              {busy ? "Signing in..." : "Login"}
              <CornerUpLeft className="h-4 w-4" />
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

type SuggestionItem =
  | {
      id: string;
      label: string;
      type: "action";
      shortcut?: string;
      run: () => void;
    }
  | {
      id: string;
      label: string;
      type: "job";
      jobName: string;
    }
  | {
      id: string;
      label: string;
      type: "route";
      description: string;
      view: "jobs" | "actions";
    };

export default function App() {
  function readUrlState() {
    if (typeof window === "undefined") {
      return { job: null, run: null, page: 0 };
    }
    const params = new URLSearchParams(window.location.search);
    const pageParam = Number.parseInt(params.get("page") ?? "1", 10);
    return {
      job: params.get("job"),
      run: params.get("run"),
      page: Number.isFinite(pageParam) && pageParam > 1 ? pageParam - 1 : 0
    };
  }

  const initialUrlState = readUrlState();
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const stored = window.localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const [authRequired, setAuthRequired] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [runs, setRuns] = useState<RunEntry[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [highlightIndex, setHighlightIndex] = useState(0);
  const [selectedJob, setSelectedJob] = useState<string | null>(initialUrlState.job);
  const [page, setPage] = useState(initialUrlState.page);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(initialUrlState.run);
  const [logLoading, setLogLoading] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);
  const [logData, setLogData] = useState<{ logpath: string; content: string } | null>(null);
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "error">("idle");
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandView, setCommandView] = useState<"root" | "jobs" | "actions">("root");
  const [listIndex, setListIndex] = useState(0);
  const [shortcutOpen, setShortcutOpen] = useState(false);
  const [failedOnly, setFailedOnly] = useState(false);
  const [focusedRunId, setFocusedRunId] = useState<string | null>(null);
  const [focusedRun, setFocusedRun] = useState<{ id: string; jobName: string } | null>(null);
  const [hoveredRun, setHoveredRun] = useState<{ id: string; jobName: string } | null>(null);
  const [runListIndex, setRunListIndex] = useState(0);

  const commandInputRef = useRef<HTMLInputElement>(null);
  const listRefs = useRef<Array<HTMLDivElement | null>>([]);
  const runListRefs = useRef<Array<HTMLDivElement | null>>([]);
  const listboxRef = useRef<HTMLDivElement | null>(null);
  const commandListRef = useRef<HTMLDivElement | null>(null);
  const commandItemRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const hasHydratedRef = useRef(false);
  const copyResetRef = useRef<number | null>(null);

  function clearStoredAuth() {
    clearAuthHeader();
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    }
    setLoginPassword("");
  }

  function saveStoredAuth(username: string, password: string) {
    if (typeof window === "undefined") return;
    window.sessionStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ username, password })
    );
  }

  async function handleCopyPath(path?: string | null) {
    if (!path) return;
    try {
      await navigator.clipboard.writeText(path);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("error");
    } finally {
      if (copyResetRef.current) window.clearTimeout(copyResetRef.current);
      copyResetRef.current = window.setTimeout(() => setCopyStatus("idle"), 1600);
    }
  }

  async function loadRuns() {
    setLoading(true);
    setError(null);
    try {
      await detectNoAuthMode();
      const data = await fetchRuns({ limit: 500 });
      setRuns(data);
      setAuthRequired(false);
      setAuthError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearStoredAuth();
        setAuthRequired(true);
        setAuthError(null);
      } else {
        setError((err as Error).message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!loginUsername || !loginPassword) {
      setAuthError("Username and password are required.");
      return;
    }
    setAuthBusy(true);
    setAuthError(null);
    setAuthHeader(loginUsername, loginPassword);
    try {
      await fetchRuns({ limit: 1 });
      saveStoredAuth(loginUsername, loginPassword);
      setAuthRequired(false);
      await loadRuns();
    } catch (err) {
      clearStoredAuth();
      if (err instanceof ApiError && err.status === 401) {
        setAuthError("Invalid username or password.");
      } else {
        setAuthError("Unable to reach the server.");
      }
    } finally {
      setAuthBusy(false);
    }
  }

  function handleLogout() {
    clearStoredAuth();
    setAuthRequired(true);
    setRuns([]);
    setSelectedJob(null);
    setSelectedRunId(null);
    setFocusedRunId(null);
    setFocusedRun(null);
    setLogData(null);
    setLogError(null);
  }

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.sessionStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored) as { username?: string; password?: string };
      if (parsed.username && parsed.password) {
        setAuthHeader(parsed.username, parsed.password);
        setLoginUsername(parsed.username);
        setLoginPassword(parsed.password);
      }
    } catch {
      window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    function syncFromUrl() {
      const state = readUrlState();
      setSelectedJob(state.job);
      setSelectedRunId(state.run);
      setPage(state.page);
      setFocusedRunId(state.run);
      setFocusedRun(state.run && state.job ? { id: state.run, jobName: state.job } : null);
    }

    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setShortcutOpen(false);
        setCommandView("root");
        setQuery("");
        setCommandOpen(true);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (commandOpen) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.isContentEditable) {
        return;
      }
      if (event.key.toLowerCase() === "d") {
        event.preventDefault();
        setTheme((current) => (current === "dark" ? "light" : "dark"));
      }
      if (event.key.toLowerCase() === "r") {
        event.preventDefault();
        loadRuns();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [commandOpen, loadRuns]);

  useEffect(() => {
    if (!commandOpen) return;
    setHighlightIndex(0);
    const timer = window.setTimeout(() => {
      commandInputRef.current?.focus();
      commandInputRef.current?.select();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [commandOpen]);

  function focusListIndex(nextIndex: number) {
    setListIndex(nextIndex);
    listRefs.current[nextIndex]?.focus();
  }

  const jobs = useMemo(() => {
    const map = new Map<string, RunEntry[]>();
    runs.forEach((run) => {
      const list = map.get(run.name) ?? [];
      list.push(run);
      map.set(run.name, list);
    });
    return Array.from(map.entries())
      .map(([name, entries]) => {
        const sorted = [...entries].sort(
          (a, b) => Date.parse(b.start) - Date.parse(a.start)
        );
        return {
          name,
          runs: sorted,
          latest: sorted[0]
        };
      })
      .sort((a, b) => Date.parse(b.latest.start) - Date.parse(a.latest.start));
  }, [runs]);

  const filteredJobs = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return jobs;
    return jobs.filter((job) => job.name.toLowerCase().includes(normalized));
  }, [jobs, query]);

  const selectedJobData = useMemo(() => {
    if (!selectedJob) return null;
    return jobs.find((job) => job.name === selectedJob) ?? null;
  }, [jobs, selectedJob]);

  useEffect(() => {
    if (!runs.length || !selectedRunId || selectedJob) return;
    const run = runs.find((entry) => entry.id === selectedRunId);
    if (!run) return;
    setSelectedJob(run.name);
  }, [runs, selectedJob, selectedRunId]);

  useEffect(() => {
    if (!hasHydratedRef.current) {
      hasHydratedRef.current = true;
      return;
    }
    setPage(0);
  }, [selectedJob]);

  useEffect(() => {
    if (!selectedJob) return;
    setPage(0);
  }, [failedOnly, selectedJob]);

  useEffect(() => {
    setListIndex(0);
  }, [filteredJobs.length]);

  useEffect(() => {
    if (!selectedRunId) {
      setLogData(null);
      setLogError(null);
      setLogLoading(false);
      return;
    }
    let active = true;
    setLogLoading(true);
    setLogError(null);
    setLogData(null);
    fetchLog(selectedRunId)
      .then((data) => {
        if (!active) return;
        setLogData(data);
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          clearStoredAuth();
          setAuthRequired(true);
          setAuthError(null);
          return;
        }
        setLogError((err as Error).message);
      })
      .finally(() => {
        if (!active) return;
        setLogLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedRunId || selectedJob) return;
    const match = runs.find((run) => run.id === selectedRunId);
    if (match) {
      setSelectedJob(match.name);
    }
  }, [runs, selectedJob, selectedRunId]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (commandOpen || selectedJob) return;
      if (!filteredJobs.length) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.isContentEditable) {
        return;
      }
      if (listboxRef.current && target && listboxRef.current.contains(target)) {
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        focusListIndex(Math.min(filteredJobs.length - 1, listIndex + 1));
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        focusListIndex(Math.max(0, listIndex - 1));
      }
      if (event.key === "Home") {
        event.preventDefault();
        focusListIndex(0);
      }
      if (event.key === "End") {
        event.preventDefault();
        focusListIndex(filteredJobs.length - 1);
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        const job = filteredJobs[listIndex];
        if (!job) return;
        const recentRuns = job.runs.slice(0, MAX_RECENT_RUNS);
        if (!recentRuns.length) return;
        const baseId =
          focusedRun && focusedRun.jobName === job.name ? focusedRun.id : recentRuns[0].id;
        const currentIndex = recentRuns.findIndex((run) => run.id === baseId);
        const nextIndex = Math.min(recentRuns.length - 1, Math.max(0, currentIndex) + 1);
        const run = recentRuns[nextIndex];
        if (run) setFocusedRun({ id: run.id, jobName: job.name });
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        const job = filteredJobs[listIndex];
        if (!job) return;
        const recentRuns = job.runs.slice(0, MAX_RECENT_RUNS);
        if (!recentRuns.length) return;
        const baseId =
          focusedRun && focusedRun.jobName === job.name ? focusedRun.id : recentRuns[0].id;
        const currentIndex = recentRuns.findIndex((run) => run.id === baseId);
        const nextIndex = Math.max(0, (currentIndex === -1 ? 0 : currentIndex) - 1);
        const run = recentRuns[nextIndex];
        if (run) setFocusedRun({ id: run.id, jobName: job.name });
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const job = filteredJobs[listIndex];
        if (!job) return;
        if (focusedRun && focusedRun.jobName === job.name) {
          const run = job.runs.find((entry) => entry.id === focusedRun.id);
          if (run) {
            handleSelectRun(job.name, run);
            return;
          }
        }
        handleSelectJob(job.name);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [commandOpen, filteredJobs, focusedRun, listIndex, selectedJob]);

  const filteredRuns = selectedJobData
    ? failedOnly
      ? selectedJobData.runs.filter((run) => run.status === "fail")
      : selectedJobData.runs
    : [];
  const pageCount = selectedJobData
    ? Math.max(1, Math.ceil(filteredRuns.length / RUNS_PER_PAGE))
    : 1;
  const pageRuns = selectedJobData
    ? filteredRuns.slice(page * RUNS_PER_PAGE, (page + 1) * RUNS_PER_PAGE)
    : [];

  const selectedRun = selectedJobData
    ? selectedJobData.runs.find((run) => run.id === selectedRunId) ?? null
    : null;

  useEffect(() => {
    if (selectedRunId) return;
    setRunListIndex(0);
    runListRefs.current[0]?.focus();
  }, [page, selectedJob, filteredRuns.length, selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) {
      setLogData(null);
      setLogError(null);
      setLogLoading(false);
      return;
    }
    let cancelled = false;
    setLogLoading(true);
    setLogError(null);
    fetchLog(selectedRunId)
      .then((data) => {
        if (cancelled) return;
        setLogData(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setLogError((err as Error).message);
        setLogData(null);
      })
      .finally(() => {
        if (cancelled) return;
        setLogLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedJobData || !selectedRunId) return;
    const index = filteredRuns.findIndex((run) => run.id === selectedRunId);
    if (index === -1) return;
    setPage(Math.floor(index / RUNS_PER_PAGE));
  }, [filteredRuns, selectedJobData, selectedRunId]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!selectedJob) return;
      if (commandOpen) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.isContentEditable) {
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        if (selectedRunId && selectedJob) {
          setSelectedRunId(null);
          setFocusedRunId(null);
          setFocusedRun(null);
          updateUrl(selectedJob, null);
        } else {
          setSelectedJob(null);
          setSelectedRunId(null);
          setFocusedRunId(null);
          setFocusedRun(null);
          updateUrl(null, null);
        }
      }
      if (event.key.toLowerCase() === "f") {
        event.preventDefault();
        setFailedOnly((current) => !current);
      }
      if (event.key === "ArrowDown") {
        if (selectedRunId) return;
        event.preventDefault();
        const nextIndex = Math.min(pageRuns.length - 1, runListIndex + 1);
        setRunListIndex(nextIndex);
        runListRefs.current[nextIndex]?.focus();
        const run = pageRuns[nextIndex];
        if (run) {
          setFocusedRunId(run.id);
        }
      }
      if (event.key === "ArrowUp") {
        if (selectedRunId) return;
        event.preventDefault();
        const nextIndex = Math.max(0, runListIndex - 1);
        setRunListIndex(nextIndex);
        runListRefs.current[nextIndex]?.focus();
        const run = pageRuns[nextIndex];
        if (run) {
          setFocusedRunId(run.id);
        }
      }
      if (!event.altKey && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
        if (selectedRunId) return;
        const recentRuns = filteredRuns.slice(0, MAX_RECENT_RUNS);
        if (!recentRuns.length) return;
        event.preventDefault();
        const baseId = focusedRunId ?? selectedRunId;
        const currentIndex = baseId ? recentRuns.findIndex((run) => run.id === baseId) : -1;
        const nextIndex =
          event.key === "ArrowRight"
            ? Math.min(recentRuns.length - 1, currentIndex + 1)
            : Math.max(0, currentIndex === -1 ? recentRuns.length - 1 : currentIndex - 1);
        const run = recentRuns[nextIndex];
        if (run) {
          setFocusedRunId(run.id);
          const listIndexMatch = pageRuns.findIndex((entry) => entry.id === run.id);
          if (listIndexMatch !== -1) {
            setRunListIndex(listIndexMatch);
            runListRefs.current[listIndexMatch]?.focus();
          }
        }
        return;
      }
      if (event.key === "Enter") {
        const targetId = selectedRunId ?? focusedRunId;
        if (!targetId) return;
        const run = filteredRuns.find((entry) => entry.id === targetId);
        if (!run) return;
        event.preventDefault();
        handleSelectRunWithinJob(run);
      }
      if (event.altKey && event.key === "ArrowLeft") {
        event.preventDefault();
        setPage((current) => Math.max(0, current - 1));
      }
      if (event.altKey && event.key === "ArrowRight") {
        event.preventDefault();
        setPage((current) => Math.min(pageCount - 1, current + 1));
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [commandOpen, filteredRuns, focusedRunId, pageCount, pageRuns.length, runListIndex, selectedJob, selectedRunId]);

  const isDark = theme === "dark";
  const stackDepth = selectedJobData ? (selectedRunId ? 2 : 1) : 0;
  const cardState = (level: number) => {
    if (level === stackDepth) return "active";
    if (level === stackDepth - 1) return "back-1";
    if (level === stackDepth - 2) return "back-2";
    return "hidden";
  };
  const headerButtonClass =
    "inline-flex h-8 items-center gap-1.5 rounded-full border border-ink/10 bg-white/80 px-3 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100";
  const headerKeycapClass =
    "hidden sm:inline-block rounded-full border border-ink/10 px-1.5 py-0.5 text-[9px] text-ink/40 dark:border-white/10 dark:text-slate-400";

  const actionItems: SuggestionItem[] = useMemo(() => {
    const actions: SuggestionItem[] = [
      {
        id: "refresh",
        label: "Refresh job list",
        type: "action",
        shortcut: "R",
        run: () => loadRuns()
      },
      {
        id: "theme",
        label: isDark ? "Switch to light mode" : "Switch to dark mode",
        type: "action",
        shortcut: "D",
        run: () => setTheme(isDark ? "light" : "dark")
      },
      {
        id: "shortcuts",
        label: "Keyboard shortcut overview",
        type: "action",
        shortcut: "?",
        run: () => setShortcutOpen(true)
      }
    ];

    if (selectedJob) {
      actions.push({
        id: "back",
        label: "Back to all jobs",
        type: "action",
        shortcut: "Esc",
        run: () => {
          setSelectedJob(null);
          setSelectedRunId(null);
          setFocusedRunId(null);
          setFocusedRun(null);
          updateUrl(null, null);
        }
      });
      actions.push({
        id: "failed-only",
        label: failedOnly ? "Show all runs" : "Show failed runs",
        type: "action",
        shortcut: "F",
        run: () => setFailedOnly((current) => !current)
      });
    }

    if (query.trim()) {
      actions.push({
        id: "clear",
        label: "Clear command",
        type: "action",
        shortcut: "C",
        run: () => setQuery("")
      });
    }

    return actions;
  }, [failedOnly, isDark, query, selectedJob]);

  const normalizedQuery = query.trim().toLowerCase();

  const filteredActionItems = useMemo(() => {
    if (!normalizedQuery) return actionItems;
    return actionItems.filter((action) =>
      action.label.toLowerCase().includes(normalizedQuery)
    );
  }, [actionItems, normalizedQuery]);

  const filteredJobItems = useMemo(() => {
    const base = normalizedQuery
      ? jobs.filter((job) => job.name.toLowerCase().includes(normalizedQuery))
      : jobs;
    return base.map((job) => ({
      id: `job-${job.name}`,
      label: job.name,
      type: "job" as const,
      jobName: job.name
    }));
  }, [jobs, normalizedQuery]);

  const commandItems: SuggestionItem[] = useMemo(() => {
    if (normalizedQuery) {
      return [...filteredActionItems, ...filteredJobItems];
    }
    if (commandView === "root") {
      return [
        {
          id: "route-jobs",
          label: "Search jobs",
          type: "route",
          description: `${jobs.length} jobs available`,
          view: "jobs"
        },
        {
          id: "route-actions",
          label: "Quick actions",
          type: "route",
          description: `${actionItems.length} actions`,
          view: "actions"
        }
      ];
    }
    if (commandView === "actions") {
      return filteredActionItems;
    }
    return filteredJobItems;
  }, [commandView, filteredActionItems, filteredJobItems, jobs.length, normalizedQuery]);

  useEffect(() => {
    setHighlightIndex(0);
  }, [commandItems.length, commandView, query]);

  useEffect(() => {
    if (!commandOpen) return;
    const node = commandItemRefs.current[highlightIndex];
    if (node) {
      node.scrollIntoView({ block: "nearest" });
    }
  }, [commandOpen, commandItems.length, commandView, highlightIndex]);

  function handleSuggestionSelect(item: SuggestionItem) {
    if (item.type === "route") {
      setCommandView(item.view);
      setQuery("");
      return;
    }
    if (item.type === "action") {
      item.run();
      setCommandOpen(false);
      setCommandView("root");
      setQuery("");
      return;
    }
    setSelectedJob(item.jobName);
    setSelectedRunId(null);
    updateUrl(item.jobName, null);
    setCommandOpen(false);
    setCommandView("root");
    setQuery("");
  }

  function handleCommandKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      if (commandView !== "root") {
        setCommandView("root");
        setQuery("");
        return;
      }
      setQuery("");
      setCommandOpen(false);
      return;
    }
    if (!commandItems.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightIndex((index) => (index + 1) % commandItems.length);
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightIndex((index) => (index - 1 + commandItems.length) % commandItems.length);
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const item = commandItems[highlightIndex];
      if (item) handleSuggestionSelect(item);
    }
  }

  function handleListKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (commandOpen) return;
    if (!filteredJobs.length) return;
    const navKeys = ["ArrowDown", "ArrowUp", "Home", "End", "Enter"];
    if (navKeys.includes(event.key)) {
      event.stopPropagation();
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusListIndex(Math.min(filteredJobs.length - 1, listIndex + 1));
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      focusListIndex(Math.max(0, listIndex - 1));
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      const job = filteredJobs[listIndex];
      if (!job) return;
      const recentRuns = job.runs.slice(0, MAX_RECENT_RUNS);
      if (!recentRuns.length) return;
      const baseId =
        focusedRun && focusedRun.jobName === job.name ? focusedRun.id : recentRuns[0].id;
      const currentIndex = recentRuns.findIndex((run) => run.id === baseId);
      const nextIndex = Math.min(recentRuns.length - 1, Math.max(0, currentIndex) + 1);
      const run = recentRuns[nextIndex];
      if (run) setFocusedRun({ id: run.id, jobName: job.name });
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      const job = filteredJobs[listIndex];
      if (!job) return;
      const recentRuns = job.runs.slice(0, MAX_RECENT_RUNS);
      if (!recentRuns.length) return;
      const baseId =
        focusedRun && focusedRun.jobName === job.name ? focusedRun.id : recentRuns[0].id;
      const currentIndex = recentRuns.findIndex((run) => run.id === baseId);
      const nextIndex = Math.max(0, (currentIndex === -1 ? 0 : currentIndex) - 1);
      const run = recentRuns[nextIndex];
      if (run) setFocusedRun({ id: run.id, jobName: job.name });
    }
    if (event.key === "Home") {
      event.preventDefault();
      focusListIndex(0);
    }
    if (event.key === "End") {
      event.preventDefault();
      focusListIndex(filteredJobs.length - 1);
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const job = filteredJobs[listIndex];
      if (!job) return;
      if (focusedRun && focusedRun.jobName === job.name) {
        const run = job.runs.find((entry) => entry.id === focusedRun.id);
        if (run) {
          handleSelectRun(job.name, run);
          return;
        }
      }
      handleSelectJob(job.name);
    }
  }

  function updateUrl(job: string | null, run: string | null, replace = false) {
    const url = new URL(window.location.href);
    if (job) {
      url.searchParams.set("job", job);
    } else {
      url.searchParams.delete("job");
    }
    if (run) {
      url.searchParams.set("run", run);
    } else {
      url.searchParams.delete("run");
    }
    if (job && page > 0) {
      url.searchParams.set("page", String(page + 1));
    } else {
      url.searchParams.delete("page");
    }
    if (replace) {
      window.history.replaceState({}, "", url);
    } else {
      window.history.pushState({}, "", url);
    }
  }

  useEffect(() => {
    if (typeof window === "undefined") return;
    updateUrl(selectedJob, selectedRunId, true);
  }, [page, selectedJob, selectedRunId]);

  function handleSelectJob(name: string) {
    setSelectedJob(name);
    setSelectedRunId(null);
    setFocusedRunId(null);
    setFocusedRun(null);
    updateUrl(name, null);
  }

  function handleSelectRun(jobName: string, run: RunEntry) {
    setSelectedJob(jobName);
    setSelectedRunId(run.id);
    setFocusedRunId(run.id);
    setFocusedRun(null);
    updateUrl(jobName, run.id);
  }

  function handleSelectRunWithinJob(run: RunEntry) {
    setSelectedRunId(run.id);
    setFocusedRunId(run.id);
    setFocusedRun(null);
    updateUrl(selectedJob ?? run.name, run.id);
  }
  const shortcutGroups = [
    {
      title: "Global",
      items: [{ label: "Open command palette", keys: "Cmd/Ctrl + K" }]
    },
    {
      title: "Command palette",
      items: [
        { label: "Move selection", keys: "Up / Down" },
        { label: "Open selection", keys: "Enter" },
        { label: "Close palette", keys: "Esc" }
      ]
    },
    {
      title: "Job list",
      items: [
        { label: "Move selection", keys: "Up / Down" },
        { label: "Move run focus", keys: "Left / Right" },
        { label: "Jump to start/end", keys: "Home / End" },
        { label: "Open job/run", keys: "Enter" }
      ]
    },
    {
      title: "Job detail",
      items: [
        { label: "Back to list", keys: "Esc" },
        { label: "Toggle failed runs", keys: "F" },
        { label: "Move run focus", keys: "Up / Down" },
        { label: "Move bar focus", keys: "Left / Right" },
        { label: "Previous / next page", keys: "Alt + ← / Alt + →" }
      ]
    }
  ];

  if (authRequired && !isStaticMode()) {
    return (
      <LoginScreen
        theme={theme}
        onToggleTheme={() => setTheme(isDark ? "light" : "dark")}
        onSubmit={handleLogin}
        error={authError}
        busy={authBusy}
        username={loginUsername}
        password={loginPassword}
        onUsernameChange={setLoginUsername}
        onPasswordChange={setLoginPassword}
      />
    );
  }
  return (
    <div className="app-shell">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-4 px-3 py-6 sm:gap-6 sm:px-6 sm:py-10">
        <header className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-plum dark:text-orange-300">Skedulord</p>
            <nav aria-label="Breadcrumb">
              <ol className="flex flex-wrap items-center gap-3 text-sm uppercase tracking-[0.3em]">
                {selectedJobData ? (
                  <>
                    <li>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedJob(null);
                          setSelectedRunId(null);
                          setFocusedRunId(null);
                          setFocusedRun(null);
                          updateUrl(null, null);
                        }}
                        className="uppercase text-ink/50 transition hover:text-ink dark:text-slate-400 dark:hover:text-slate-200"
                      >
                        All jobs
                      </button>
                    </li>
                    <li aria-hidden="true" className="text-ink/30 dark:text-slate-500">
                      /
                    </li>
                  </>
                ) : null}
                {selectedJobData && selectedRunId ? (
                  <>
                    <li>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedRunId(null);
                          setFocusedRunId(null);
                          setFocusedRun(null);
                          updateUrl(selectedJobData.name, null);
                        }}
                        className="uppercase text-ink/50 transition hover:text-ink dark:text-slate-400 dark:hover:text-slate-200"
                      >
                        {selectedJobData.name}
                      </button>
                    </li>
                    <li aria-hidden="true" className="text-ink/30 dark:text-slate-500">
                      /
                    </li>
                    <li aria-current="page" className="font-semibold uppercase text-ink dark:text-slate-100">
                      Run {selectedRunId.slice(0, 8)}
                    </li>
                  </>
                ) : (
                  <li aria-current="page" className="font-semibold uppercase text-ink dark:text-slate-100">
                    {selectedJobData ? selectedJobData.name : "All jobs"}
                  </li>
                )}
              </ol>
            </nav>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-end">
            <button
              onClick={() => {
                setCommandView("root");
                setQuery("");
                setCommandOpen(true);
              }}
              className={headerButtonClass}
              aria-label="Open command palette"
            >
              <Command className="h-4 w-4" />
              <span className="hidden sm:inline">Cmd + K</span>
            </button>
            <button
              onClick={() => setTheme(isDark ? "light" : "dark")}
              className={headerButtonClass}
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {isDark ? "Light" : "Dark"}
              <span className={headerKeycapClass}>D</span>
            </button>
            <button
              onClick={loadRuns}
              className={headerButtonClass}
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
              <span className={headerKeycapClass}>R</span>
            </button>
            {!isStaticMode() && !isNoAuthMode() && (
              <button
                onClick={handleLogout}
                className={headerButtonClass}
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            )}
          </div>
        </header>

        {error ? (
          <div className="flex items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        ) : null}

        <div className="card-stack">
          <section
            className="card-layer frost-card flex flex-col gap-5 rounded-3xl p-6 shadow-card"
            data-state={cardState(0)}
            aria-hidden={stackDepth !== 0}
          >
            <div className="flex items-center justify-end">
              <p className="text-xs text-ink/60 dark:text-slate-300">{filteredJobs.length} jobs</p>
            </div>

            <div
              className="overflow-hidden rounded-2xl border border-ink/5 bg-white/80 dark:border-white/10 dark:bg-slate-900/70"
              role="listbox"
              aria-label="Jobs"
              onKeyDown={handleListKeyDown}
              tabIndex={stackDepth === 0 ? 0 : -1}
              ref={listboxRef}
            >
              <ScrollArea.Root className="h-[320px] sm:h-[420px] lg:h-[520px] overflow-hidden" type="scroll">
                <ScrollArea.Viewport className="h-full w-full p-2">
                  <div className="flex flex-col gap-2">
                    {loading ? (
                      <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">Loading jobs...</p>
                    ) : null}
                    {!loading && filteredJobs.length === 0 ? (
                      <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">No jobs match this search.</p>
                    ) : null}
                    {filteredJobs.map((job, index) => {
                      const hoveredForJob =
                        hoveredRun && hoveredRun.jobName === job.name
                          ? job.runs.find((run) => run.id === hoveredRun.id) ?? null
                          : null;
                      const focusedForJob =
                        focusedRun && focusedRun.jobName === job.name
                          ? job.runs.find((run) => run.id === focusedRun.id) ?? null
                          : null;
                      const detailRun = hoveredForJob ?? focusedForJob ?? job.latest ?? null;

                      return (
                        <div
                          key={job.name}
                          ref={(node) => {
                            listRefs.current[index] = node;
                          }}
                          onClick={() => handleSelectJob(job.name)}
                          className={`cursor-pointer rounded-2xl border px-4 py-3 text-left text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                            index === listIndex
                              ? "border-ink/20 bg-white shadow-soft dark:border-white/10 dark:bg-slate-900"
                              : "border-transparent hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900/60"
                          }`}
                          aria-selected={index === listIndex}
                          role="option"
                          tabIndex={-1}
                        >
                          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
                            <div className="min-w-0">
                              <p className="truncate font-medium text-ink dark:text-slate-100">{job.name}</p>
                              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink/50 dark:text-slate-400">
                                <span>{job.runs.length} runs in view</span>
                                {detailRun ? (
                                  <span className="flex items-center gap-1">
                                    <span className={`h-1.5 w-1.5 rounded-full ${statusColor(detailRun.status, detailRun.attempt)}`} />
                                    {hoveredForJob || focusedForJob ? "Run" : "Last run"}{" "}
                                    {formatDuration(getDurationMs(detailRun))}
                                    {hoveredForJob || focusedForJob
                                      ? ` · ${detailRun.id.slice(0, 6)} · ${detailRun.status}${detailRun.attempt > 1 ? ` (${detailRun.attempt} attempts)` : ""}`
                                      : ""}
                                  </span>
                                ) : null}
                              </div>
                            </div>
                            <div className="w-full overflow-x-auto sm:w-auto sm:shrink-0 sm:overflow-visible">
                              <RunBars
                                runs={job.runs}
                                variant="compact"
                                onSelectRun={(run) => handleSelectRun(job.name, run)}
                                onHoverRun={(run) => {
                                  if (!run) {
                                    setHoveredRun(null);
                                    return;
                                  }
                                  setHoveredRun({ id: run.id, jobName: job.name });
                                }}
                                highlightRunId={
                                  hoveredRun && hoveredRun.jobName === job.name
                                    ? hoveredRun.id
                                    : focusedRun && focusedRun.jobName === job.name
                                      ? focusedRun.id
                                      : null
                                }
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </ScrollArea.Viewport>
                <ScrollArea.Scrollbar
                  orientation="vertical"
                  className="flex w-2 touch-none select-none rounded-full bg-ink/5 p-0.5 opacity-0 transition-opacity duration-200 data-[state=visible]:opacity-100 dark:bg-white/10"
                >
                  <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/30 dark:bg-white/30" />
                </ScrollArea.Scrollbar>
              </ScrollArea.Root>
            </div>
          </section>

          <section
            className="card-layer frost-card flex flex-col gap-5 rounded-3xl p-6 shadow-card"
            data-state={cardState(1)}
            aria-hidden={stackDepth !== 1}
          >
            {selectedJobData ? (
              <>
                <div className="flex flex-wrap items-center justify-end gap-4">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedJob(null);
                        setSelectedRunId(null);
                        setFocusedRunId(null);
                        setFocusedRun(null);
                        updateUrl(null, null);
                      }}
                      className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-3 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                    >
                      <CornerUpLeft className="h-3 w-3" />
                      Back
                      <span className="hidden sm:inline-block rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                        Esc
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setFailedOnly((current) => !current)}
                      className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-3 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                    >
                      <Filter className="h-3 w-3" />
                      {failedOnly ? "Show all" : "Failed only"}
                      <span className="hidden sm:inline-block rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                        F
                      </span>
                    </button>
                    {selectedJobData.latest ? <StatusPill status={selectedJobData.latest.status} attempt={selectedJobData.latest.attempt} /> : null}
                  </div>
                </div>

                <div className="rounded-2xl border border-ink/10 bg-white/80 p-4 dark:border-white/10 dark:bg-slate-900/70">
                  <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                    <p className="font-semibold text-ink dark:text-slate-100">Recent run durations</p>
                    <p className="text-xs text-ink/60 dark:text-slate-300">
                      {failedOnly ? "Failed runs only" : `Last ${MAX_RECENT_RUNS} runs`}
                    </p>
                  </div>
                  <div className="mt-4">
                    <RunBars
                      runs={filteredRuns}
                      onSelectRun={handleSelectRunWithinJob}
                      highlightRunId={focusedRunId ?? selectedRunId}
                    />
                  </div>
                </div>

                <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/5 px-4 py-3 text-xs uppercase tracking-[0.2em] text-clay dark:border-white/10 dark:text-slate-400">
                    <span>{failedOnly ? "Failed runs" : "Runs"}</span>
                    <span>
                      Page {page + 1} of {pageCount}
                    </span>
                  </div>
                  <ScrollArea.Root className="h-[280px] sm:h-[350px] lg:h-[420px] overflow-hidden" type="scroll">
                    <ScrollArea.Viewport className="h-full w-full p-2">
                      <div className="flex flex-col gap-2">
                        {pageRuns.length === 0 ? (
                          <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">
                            {failedOnly ? "No failed runs for this job." : "No runs for this job."}
                          </p>
                        ) : (
                          pageRuns.map((run, index) => (
                            <div
                              key={run.id}
                              ref={(node) => {
                                runListRefs.current[index] = node;
                              }}
                              tabIndex={-1}
                              className={`flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-3 rounded-2xl border px-4 py-3 text-sm transition ${
                                run.id === selectedRunId || run.id === focusedRunId
                                  ? "border-ink/20 bg-white shadow-soft dark:border-white/10 dark:bg-slate-900"
                                  : "border-transparent hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900"
                              }`}
                              onClick={() => handleSelectRunWithinJob(run)}
                            >
                              <div>
                                <p className="font-medium text-ink dark:text-slate-100">Run {run.id.slice(0, 6)}</p>
                                <p className="text-xs text-ink/50 dark:text-slate-400">{run.command}</p>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-xs text-ink/60 dark:text-slate-300">
                                  {formatDuration(getDurationMs(run))}
                                </span>
                                <StatusPill status={run.status} attempt={run.attempt} />
                                <span className="rounded-full border border-ink/10 px-2 py-0.5 text-[11px] font-semibold text-ink/50 dark:border-white/10 dark:text-slate-300">
                                  Logs
                                </span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </ScrollArea.Viewport>
                    <ScrollArea.Scrollbar
                      orientation="vertical"
                      className="flex w-2 touch-none select-none rounded-full bg-ink/5 p-0.5 opacity-0 transition-opacity duration-200 data-[state=visible]:opacity-100 dark:bg-white/10"
                    >
                      <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/30 dark:bg-white/30" />
                    </ScrollArea.Scrollbar>
                  </ScrollArea.Root>
                </div>
                <div className="flex items-center justify-between px-2 text-sm">
                  <button
                    type="button"
                    onClick={() => setPage((current) => Math.max(0, current - 1))}
                    disabled={page === 0}
                    className="rounded-full border border-ink/10 bg-white/80 px-3 py-1 text-xs font-semibold text-ink shadow-sm transition disabled:opacity-40 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                  >
                    Previous
                    <span className="ml-2 hidden sm:inline-block rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                      ←
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
                    disabled={page + 1 >= pageCount}
                    className="rounded-full border border-ink/10 bg-white/80 px-3 py-1 text-xs font-semibold text-ink shadow-sm transition disabled:opacity-40 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                  >
                    Next
                    <span className="ml-2 hidden sm:inline-block rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                      →
                    </span>
                  </button>
                </div>

                <div className="rounded-2xl border border-ink/10 bg-white/80 p-4 dark:border-white/10 dark:bg-slate-900/70">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Run log</p>
                      <h3 className="font-display text-xl text-ink dark:text-slate-100">
                        {selectedRunId ? `Run ${selectedRunId.slice(0, 8)}` : "Select a run"}
                      </h3>
                    </div>
                    {selectedRunId ? (
                      <button
                        type="button"
                        onClick={() => setSelectedRunId(null)}
                        className="rounded-full border border-ink/10 px-3 py-1 text-xs font-semibold text-ink transition dark:border-white/10 dark:text-slate-100"
                      >
                        Close
                      </button>
                    ) : null}
                  </div>
                  {selectedRunId ? (
                    <div className="mt-4 space-y-3 text-sm">
                      {logError ? (
                        <p className="rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
                          {logError}
                        </p>
                      ) : null}
                      {logLoading ? (
                        <p className="text-ink/60 dark:text-slate-300">Loading log…</p>
                      ) : null}
                      {logData ? (
                        <>
                          <div className="flex flex-wrap items-center gap-2 text-xs text-ink/60 dark:text-slate-300">
                            <span className="font-mono" title={logData.logpath}>
                              {filenameOnly(logData.logpath)}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleCopyPath(logData.logpath)}
                              className="inline-flex items-center gap-1 rounded-full border border-ink/10 px-2 py-0.5 text-[10px] font-semibold text-ink/70 transition hover:-translate-y-0.5 hover:shadow-card dark:border-white/10 dark:text-slate-200"
                              aria-label="Copy log path"
                            >
                              {copyStatus === "copied" ? (
                                <Check className="h-3 w-3" />
                              ) : copyStatus === "error" ? (
                                <AlertCircle className="h-3 w-3 text-rose-500" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                              {copyStatus === "copied" ? "Copied" : "Copy"}
                            </button>
                          </div>
                          <pre className="max-h-[200px] sm:max-h-[280px] lg:max-h-[320px] overflow-auto rounded-2xl border border-ink/10 bg-white px-4 py-3 text-xs text-ink dark:border-white/10 dark:bg-slate-950 dark:text-slate-100">
                            {logData.content || "Log is empty."}
                          </pre>
                        </>
                      ) : null}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-ink/60 dark:text-slate-300">
                      Click a run to open its logs and share the URL if you need help debugging.
                    </p>
                  )}
                </div>
              </>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-ink/10 px-6 py-20 text-center text-sm text-ink/60 dark:border-white/10 dark:text-slate-300">
                <p className="text-xs uppercase tracking-[0.3em] text-plum dark:text-orange-300">Job overview</p>
                <p className="text-lg font-display text-ink dark:text-slate-100">Pick a job to stack forward.</p>
                <p className="max-w-md text-xs text-ink/60 dark:text-slate-400">
                  Use the list, recent run bars, or the command palette to jump straight into a run.
                </p>
              </div>
            )}
          </section>

          <section
            className="card-layer frost-card flex flex-col gap-5 rounded-3xl p-6 shadow-card"
            data-state={cardState(2)}
            aria-hidden={stackDepth !== 2}
          >
            {selectedJobData && selectedRunId ? (
              <>
                <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Run details</p>
                    <h2 className="font-display text-2xl text-ink dark:text-slate-100">
                      {selectedJobData.name}
                    </h2>
                    {selectedRun ? (
                      <p className="mt-1 text-xs text-ink/60 dark:text-slate-300">
                        Run {selectedRun.id.slice(0, 8)} · {formatDuration(getDurationMs(selectedRun))} · {selectedRun.status}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedRunId(null);
                        setFocusedRunId(null);
                        setFocusedRun(null);
                        updateUrl(selectedJobData.name, null);
                      }}
                      className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-3 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                    >
                      <CornerUpLeft className="h-3 w-3" />
                      Back to runs
                      <span className="hidden sm:inline-block rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                        Esc
                      </span>
                    </button>
                  </div>
                </div>

                <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/5 px-4 py-3 text-xs uppercase tracking-[0.2em] text-clay dark:border-white/10 dark:text-slate-400">
                    <span>Run log</span>
                    <div className="flex flex-wrap items-center gap-2">
                      {selectedRun ? (
                        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-ink/10 bg-white/70 px-3 py-1 text-[10px] font-semibold normal-case text-ink/70 shadow-sm dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-200">
                          <span
                            className="font-mono text-ink/60 dark:text-slate-300"
                            title={selectedRun.logpath}
                          >
                            {filenameOnly(selectedRun.logpath)}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleCopyPath(selectedRun.logpath)}
                            className="inline-flex items-center gap-1 rounded-full border border-ink/10 px-2 py-0.5 text-[10px] font-semibold text-ink/70 transition hover:-translate-y-0.5 hover:shadow-card dark:border-white/10 dark:text-slate-200"
                            aria-label="Copy log path"
                          >
                            {copyStatus === "copied" ? (
                              <Check className="h-3 w-3" />
                            ) : copyStatus === "error" ? (
                              <AlertCircle className="h-3 w-3 text-rose-500" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                            {copyStatus === "copied" ? "Copied" : "Copy"}
                          </button>
                        </div>
                      ) : null}
                    </div>
                  </div>
                  <ScrollArea.Root className="h-[320px] sm:h-[420px] lg:h-[520px]">
                    <ScrollArea.Viewport className="p-4">
                      {selectedRun ? (
                        logLoading ? (
                          <p className="text-sm text-ink/50 dark:text-slate-400">Loading log…</p>
                        ) : logError ? (
                          <p className="text-sm text-rose-600 dark:text-rose-300">{logError}</p>
                        ) : logData ? (
                          <pre className="whitespace-pre-wrap text-xs leading-relaxed text-ink dark:text-slate-100">
                            {logData.content || "Log is empty."}
                          </pre>
                        ) : (
                          <p className="text-sm text-ink/50 dark:text-slate-400">No log available.</p>
                        )
                      ) : (
                        <p className="text-sm text-ink/50 dark:text-slate-400">
                          Select a run to view its logs.
                        </p>
                      )}
                    </ScrollArea.Viewport>
                    <ScrollArea.Scrollbar orientation="vertical" className="flex touch-none select-none p-1">
                      <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/20 dark:bg-white/20" />
                    </ScrollArea.Scrollbar>
                  </ScrollArea.Root>
                </div>
              </>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-ink/10 px-6 py-20 text-center text-sm text-ink/60 dark:border-white/10 dark:text-slate-300">
                <p className="text-xs uppercase tracking-[0.3em] text-plum dark:text-orange-300">Run detail</p>
                <p className="text-lg font-display text-ink dark:text-slate-100">Select a run to see logs.</p>
                <p className="max-w-md text-xs text-ink/60 dark:text-slate-400">
                  Use the arrow keys to focus a run, then hit Enter to drill into logs.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>

      {commandOpen ? (
        <div
          className="fixed inset-0 z-50 flex justify-center bg-black/30 px-3 py-8 sm:px-4 sm:py-20 backdrop-blur-sm dark:bg-black/60"
          onClick={() => {
            setCommandOpen(false);
            setCommandView("root");
            setQuery("");
          }}
          role="presentation"
        >
          <div
            className="w-full max-w-[calc(100%-1rem)] sm:max-w-xl rounded-3xl border border-ink/10 bg-white/95 p-4 shadow-soft dark:border-white/10 dark:bg-slate-950/90"
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            onClick={(event) => event.stopPropagation()}
            onKeyDown={handleCommandKeyDown}
          >
            <div className="flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/70 px-3 py-2 text-sm text-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100">
              <Search className="h-4 w-4 text-ink/40 dark:text-slate-400" />
              <input
                ref={commandInputRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={
                  normalizedQuery
                    ? "Search jobs or actions…"
                    : commandView === "actions"
                      ? "Type an action…"
                      : "Type a job name…"
                }
                className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40 dark:placeholder:text-slate-400"
              />
              <span className="hidden sm:inline text-xs text-ink/40 dark:text-slate-400">
                {commandView === "root" ? "Esc" : "Esc · Back"}
              </span>
            </div>
            <div className="mt-3 max-h-[60vh] overflow-auto" role="listbox" ref={commandListRef}>
              {commandItems.length === 0 ? (
                <p className="px-3 py-4 text-sm text-ink/50 dark:text-slate-400">No matching commands.</p>
              ) : (
                commandItems.map((item, index) => {
                  const isSelected = index === highlightIndex;
                  const isRoute = item.type === "route";
                  const selectedClass = isSelected
                    ? isRoute
                      ? "bg-ink/10 text-ink border-2 border-ink/40 dark:bg-white/10 dark:text-slate-100 dark:border-white/30"
                      : "text-ink border border-ink/35 font-semibold dark:border-white/20 dark:text-slate-100"
                    : "text-ink/70 hover:bg-ink/5 hover:text-ink dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-slate-100";

                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => handleSuggestionSelect(item)}
                      ref={(node) => {
                        commandItemRefs.current[index] = node;
                      }}
                      className={`flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                        isRoute
                          ? "gap-4 border border-ink/10 bg-white/80 px-4 py-3 text-ink shadow-card dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                          : ""
                      } ${selectedClass}`}
                      aria-selected={isSelected}
                      role="option"
                    >
                      <div>
                        <span className="block">{item.label}</span>
                        {item.type === "route" ? (
                          <span className="mt-1 block text-xs text-ink/50 dark:text-slate-400">
                            {item.description}
                          </span>
                        ) : null}
                      </div>
                      {item.type === "action" ? (
                        <span className="rounded-full border border-ink/10 px-2 py-0.5 text-xs text-ink/40 dark:border-white/10 dark:text-slate-400">
                          {item.shortcut ?? ""}
                        </span>
                      ) : item.type === "job" ? (
                        <span className="text-xs text-ink/40 dark:text-slate-400">Job</span>
                      ) : (
                        <span className="text-xs text-ink/40 dark:text-slate-400">Enter</span>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>
      ) : null}
      {shortcutOpen ? (
        <div
          className="fixed inset-0 z-50 flex justify-center bg-black/30 px-3 py-8 sm:px-4 sm:py-20 backdrop-blur-sm dark:bg-black/60"
          onClick={() => setShortcutOpen(false)}
          role="presentation"
        >
          <div
            className="w-full max-w-[calc(100%-1rem)] sm:max-w-lg rounded-3xl border border-ink/10 bg-white/95 p-6 shadow-soft dark:border-white/10 dark:bg-slate-950/90"
            role="dialog"
            aria-modal="true"
            aria-label="Keyboard shortcut overview"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">
                  Shortcuts
                </p>
                <h2 className="font-display text-2xl text-ink dark:text-slate-100">
                  Keyboard shortcut overview
                </h2>
                <p className="mt-1 text-sm text-ink/60 dark:text-slate-300">
                  Quick reference for navigation and palette controls.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShortcutOpen(false)}
                className="rounded-full border border-ink/10 px-3 py-1 text-xs font-semibold text-ink transition hover:-translate-y-0.5 hover:shadow-card dark:border-white/10 dark:text-slate-100"
              >
                Close
              </button>
            </div>
            <div className="mt-6 grid gap-4">
              {shortcutGroups.map((group) => (
                <div
                  key={group.title}
                  className="rounded-2xl border border-ink/10 bg-white/80 p-4 text-sm dark:border-white/10 dark:bg-slate-900/70"
                >
                  <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">
                    {group.title}
                  </p>
                  <div className="mt-3 space-y-2">
                    {group.items.map((item) => (
                      <div key={item.label} className="flex items-center justify-between gap-3">
                        <span className="text-ink/80 dark:text-slate-200">
                          {item.label}
                        </span>
                        <span className="rounded-full border border-ink/10 bg-white/80 px-2 py-0.5 text-xs font-semibold text-ink dark:border-white/10 dark:bg-slate-950/80 dark:text-slate-100">
                          {item.keys}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
