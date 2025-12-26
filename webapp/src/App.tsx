import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import { AlertCircle, Command, CornerUpLeft, Filter, Moon, RefreshCw, Search, Sun } from "lucide-react";

import { fetchLog, fetchRuns, type RunEntry } from "./api";

const MAX_RECENT_RUNS = 20;
const RUNS_PER_PAGE = 25;
const SUGGESTION_LIMIT = 10;

function statusColor(status: string) {
  if (status === "success") return "bg-emerald-500";
  if (status === "fail") return "bg-rose-500";
  return "bg-amber-400";
}

function StatusPill({ status }: { status: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-ink shadow-sm dark:bg-slate-900/70 dark:text-slate-100">
      <span className={`h-2 w-2 rounded-full ${statusColor(status)}`} />
      {status}
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

function RunBars({ runs }: { runs: RunEntry[] }) {
  const recentRuns = runs.slice(0, MAX_RECENT_RUNS);
  const durations = recentRuns.map((run) => getDurationMs(run));
  const maxDuration = Math.max(0, ...durations);
  const maxHeight = 52;
  const minHeight = 10;

  return (
    <div className="flex items-end gap-2" aria-label="Recent runs" role="list">
      {recentRuns.map((run, index) => {
        const duration = durations[index];
        const height = maxDuration
          ? Math.max(minHeight, Math.round((duration / maxDuration) * maxHeight))
          : minHeight;
        const label = `${run.status} run, ${formatDuration(duration)}`;

        return (
          <div
            key={run.id}
            className={`w-3 rounded-full ${statusColor(run.status)}`}
            style={{ height }}
            aria-label={label}
            role="listitem"
          />
        );
      })}
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
  const [commandOpen, setCommandOpen] = useState(false);
  const [listIndex, setListIndex] = useState(0);
  const [shortcutOpen, setShortcutOpen] = useState(false);
  const [failedOnly, setFailedOnly] = useState(false);

  const commandInputRef = useRef<HTMLInputElement>(null);
  const listRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const hasHydratedRef = useRef(false);

  async function loadRuns() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRuns({ limit: 500 });
      setRuns(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const params = url.searchParams;
    if (selectedJob) {
      params.set("job", selectedJob);
    } else {
      params.delete("job");
    }
    if (selectedRunId) {
      params.set("run", selectedRunId);
    } else {
      params.delete("run");
    }
    if (selectedJob && page > 0) {
      params.set("page", String(page + 1));
    } else {
      params.delete("page");
    }
    url.search = params.toString();
    window.history.replaceState({}, "", url.toString());
  }, [page, selectedJob, selectedRunId]);

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
    if (!hasHydratedRef.current) {
      hasHydratedRef.current = true;
      return;
    }
    setPage(0);
    setFailedOnly(false);
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
      if (event.key === "Enter") {
        event.preventDefault();
        const job = filteredJobs[listIndex];
        if (job) {
          setSelectedJob(job.name);
          setSelectedRunId(null);
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [commandOpen, filteredJobs, listIndex, selectedJob]);

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

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!selectedJob) return;
      if (commandOpen) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.isContentEditable) {
        return;
      }
      if (event.key.toLowerCase() === "b") {
        event.preventDefault();
        setSelectedJob(null);
        setSelectedRunId(null);
        setPage(0);
      }
      if (event.key.toLowerCase() === "f") {
        event.preventDefault();
        setFailedOnly((current) => !current);
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        setPage((current) => Math.max(0, current - 1));
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        setPage((current) => Math.min(pageCount - 1, current + 1));
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [commandOpen, pageCount, selectedJob]);

  const isDark = theme === "dark";
  const headerButtonClass =
    "inline-flex h-8 items-center gap-1.5 rounded-full border border-ink/10 bg-white/80 px-3 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100";
  const headerKeycapClass =
    "rounded-full border border-ink/10 px-1.5 py-0.5 text-[9px] text-ink/40 dark:border-white/10 dark:text-slate-400";

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
        shortcut: "B",
        run: () => {
          setSelectedJob(null);
          setSelectedRunId(null);
          setPage(0);
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

  const suggestionItems = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const filteredActions = normalized
      ? actionItems.filter((action) => action.label.toLowerCase().includes(normalized))
      : actionItems;
    const filteredJobItems = (normalized ? filteredJobs : jobs).map((job) => ({
      id: `job-${job.name}`,
      label: job.name,
      type: "job" as const,
      jobName: job.name
    }));

    return [...filteredActions, ...filteredJobItems].slice(0, SUGGESTION_LIMIT);
  }, [actionItems, filteredJobs, jobs, query]);

  useEffect(() => {
    setHighlightIndex(0);
  }, [query, suggestionItems.length]);

  function handleSuggestionSelect(item: SuggestionItem) {
    if (item.type === "action") {
      item.run();
      setCommandOpen(false);
      setQuery("");
      return;
    }
    setSelectedJob(item.jobName);
    setSelectedRunId(null);
    setCommandOpen(false);
    setQuery("");
  }

  function handleCommandKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!suggestionItems.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightIndex((index) => (index + 1) % suggestionItems.length);
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightIndex((index) =>
        (index - 1 + suggestionItems.length) % suggestionItems.length
      );
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const item = suggestionItems[highlightIndex];
      if (item) handleSuggestionSelect(item);
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setQuery("");
      setCommandOpen(false);
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
      if (job) {
        setSelectedJob(job.name);
        setSelectedRunId(null);
      }
    }
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
        { label: "Jump to start/end", keys: "Home / End" },
        { label: "Open job", keys: "Enter" }
      ]
    },
    {
      title: "Job detail",
      items: [
        { label: "Back to list", keys: "B" },
        { label: "Toggle failed runs", keys: "F" },
        { label: "Previous / next page", keys: "← / →" }
      ]
    }
  ];
  return (
    <div className="app-shell">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-6 py-10">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-plum dark:text-orange-300">Skedulord</p>
            <h1 className="font-display text-4xl font-semibold text-ink dark:text-slate-100">
              {selectedJobData ? selectedJobData.name : "All jobs"}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCommandOpen(true)}
              className={headerButtonClass}
              aria-label="Open command palette"
            >
              <Command className="h-4 w-4" />
              Cmd + K
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
          </div>
        </header>

        {error ? (
          <div className="flex items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        ) : null}

        {selectedJobData ? (
          <section className="frost-card flex flex-col gap-5 rounded-3xl p-6 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Job overview</p>
                <h2 className="font-display text-2xl text-ink dark:text-slate-100">{selectedJobData.name}</h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedJob(null);
                    setSelectedRunId(null);
                    setPage(0);
                  }}
                  className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-3 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                >
                  <CornerUpLeft className="h-3 w-3" />
                  Back
                  <span className="rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                    B
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setFailedOnly((current) => !current)}
                  className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-3 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                >
                  <Filter className="h-3 w-3" />
                  {failedOnly ? "Show all" : "Failed only"}
                  <span className="rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
                    F
                  </span>
                </button>
                {selectedJobData.latest ? <StatusPill status={selectedJobData.latest.status} /> : null}
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
                <RunBars runs={filteredRuns} />
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/5 px-4 py-3 text-xs uppercase tracking-[0.2em] text-clay dark:border-white/10 dark:text-slate-400">
                <span>{failedOnly ? "Failed runs" : "Runs"}</span>
                <span>
                  Page {page + 1} of {pageCount}
                </span>
              </div>
              <ScrollArea.Root className="h-[420px]">
                <ScrollArea.Viewport className="p-2">
                  <div className="flex flex-col gap-2">
                    {pageRuns.length === 0 ? (
                      <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">
                        {failedOnly ? "No failed runs for this job." : "No runs for this job."}
                      </p>
                    ) : (
                      pageRuns.map((run) => (
                        <button
                          key={run.id}
                          type="button"
                          onClick={() => setSelectedRunId(run.id)}
                          className={`flex w-full flex-wrap items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-left text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                            selectedRunId === run.id
                              ? "border-ink/20 bg-white shadow-soft dark:border-white/10 dark:bg-slate-900"
                              : "border-transparent hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900"
                          }`}
                        >
                          <div>
                            <p className="font-medium text-ink dark:text-slate-100">Run {run.id.slice(0, 6)}</p>
                            <p className="text-xs text-ink/50 dark:text-slate-400">{run.command}</p>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-ink/60 dark:text-slate-300">
                              {formatDuration(getDurationMs(run))}
                            </span>
                            <StatusPill status={run.status} />
                            <span className="rounded-full border border-ink/10 px-2 py-0.5 text-[11px] font-semibold text-ink/50 dark:border-white/10 dark:text-slate-300">
                              Logs
                            </span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </ScrollArea.Viewport>
                <ScrollArea.Scrollbar orientation="vertical" className="flex touch-none select-none p-1">
                  <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/20 dark:bg-white/20" />
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
                <span className="ml-2 rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
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
                <span className="ml-2 rounded-full border border-ink/10 px-2 py-0.5 text-[10px] text-ink/40 dark:border-white/10 dark:text-slate-400">
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
                      <p className="text-xs text-ink/60 dark:text-slate-300">{logData.logpath}</p>
                      <pre className="max-h-[320px] overflow-auto rounded-2xl border border-ink/10 bg-white px-4 py-3 text-xs text-ink dark:border-white/10 dark:bg-slate-950 dark:text-slate-100">
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
          </section>
        ) : (
          <section className="frost-card flex flex-col gap-5 rounded-3xl p-6 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Job list</p>
                <h2 className="font-display text-2xl text-ink dark:text-slate-100">All jobs</h2>
              </div>
              <p className="text-xs text-ink/60 dark:text-slate-300">
                {filteredJobs.length} jobs
              </p>
            </div>

            <div
              className="overflow-hidden rounded-2xl border border-ink/5 bg-white/80 dark:border-white/10 dark:bg-slate-900/70"
              role="listbox"
              aria-label="Jobs"
              onKeyDown={handleListKeyDown}
              tabIndex={0}
            >
              <ScrollArea.Root className="h-[520px]">
                <ScrollArea.Viewport className="p-2">
                  <div className="flex flex-col gap-2">
                    {loading ? (
                      <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">Loading jobs...</p>
                    ) : null}
                    {!loading && filteredJobs.length === 0 ? (
                      <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">No jobs match this search.</p>
                    ) : null}
                    {filteredJobs.map((job, index) => (
                      <button
                        key={job.name}
                        type="button"
                        ref={(node) => {
                          listRefs.current[index] = node;
                        }}
                        onClick={() => {
                          setSelectedJob(job.name);
                          setSelectedRunId(null);
                        }}
                        className={`rounded-2xl border px-4 py-3 text-left text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                          index === listIndex
                            ? "border-ink/20 bg-white shadow-soft dark:border-white/10 dark:bg-slate-900"
                            : "border-transparent hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900/60"
                        }`}
                        aria-selected={index === listIndex}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-ink dark:text-slate-100">{job.name}</p>
                            <p className="text-xs text-ink/50 dark:text-slate-400">{job.runs.length} runs in view</p>
                          </div>
                          {job.latest ? <StatusPill status={job.latest.status} /> : null}
                        </div>
                        <div className="mt-3">
                          <RunBars runs={job.runs} />
                        </div>
                      </button>
                    ))}
                  </div>
                </ScrollArea.Viewport>
                <ScrollArea.Scrollbar orientation="vertical" className="flex touch-none select-none p-1">
                  <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/20 dark:bg-white/20" />
                </ScrollArea.Scrollbar>
              </ScrollArea.Root>
            </div>
          </section>
        )}
      </div>

      {commandOpen ? (
        <div
          className="fixed inset-0 z-50 flex justify-center bg-black/30 px-4 py-20 backdrop-blur-sm dark:bg-black/60"
          onClick={() => {
            setCommandOpen(false);
            setQuery("");
          }}
          role="presentation"
        >
          <div
            className="w-full max-w-xl rounded-3xl border border-ink/10 bg-white/95 p-4 shadow-soft dark:border-white/10 dark:bg-slate-950/90"
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/70 px-3 py-2 text-sm text-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100">
              <Search className="h-4 w-4 text-ink/40 dark:text-slate-400" />
              <input
                ref={commandInputRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleCommandKeyDown}
                placeholder="Type a command or job name…"
                className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40 dark:placeholder:text-slate-400"
              />
              <span className="text-xs text-ink/40 dark:text-slate-400">Esc</span>
            </div>
            <div className="mt-3 max-h-64 overflow-auto" role="listbox">
              {suggestionItems.length === 0 ? (
                <p className="px-3 py-4 text-sm text-ink/50 dark:text-slate-400">No matching commands.</p>
              ) : (
                suggestionItems.map((item, index) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSuggestionSelect(item)}
                    className={`flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                      index === highlightIndex
                        ? "bg-ink/5 text-ink dark:bg-white/10 dark:text-slate-100"
                        : "text-ink/70 hover:bg-ink/5 hover:text-ink dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-slate-100"
                    }`}
                    aria-selected={index === highlightIndex}
                    role="option"
                  >
                    <span>{item.label}</span>
                    {item.type === "action" ? (
                      <span className="rounded-full border border-ink/10 px-2 py-0.5 text-xs text-ink/40 dark:border-white/10 dark:text-slate-400">
                        {item.shortcut ?? ""}
                      </span>
                    ) : (
                      <span className="text-xs text-ink/40 dark:text-slate-400">Job</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      ) : null}
      {shortcutOpen ? (
        <div
          className="fixed inset-0 z-50 flex justify-center bg-black/30 px-4 py-20 backdrop-blur-sm dark:bg-black/60"
          onClick={() => setShortcutOpen(false)}
          role="presentation"
        >
          <div
            className="w-full max-w-lg rounded-3xl border border-ink/10 bg-white/95 p-6 shadow-soft dark:border-white/10 dark:bg-slate-950/90"
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
