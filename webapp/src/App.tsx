import { useEffect, useMemo, useRef, useState } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import { AlertCircle, Command, Moon, RefreshCw, Search, Sun } from "lucide-react";

import { fetchRuns, type RunEntry } from "./api";

const MAX_RECENT_RUNS = 20;

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

type PaletteAction = {
  id: string;
  label: string;
  shortcut?: string;
  run: () => void;
};

export default function App() {
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
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [paletteIndex, setPaletteIndex] = useState(0);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const paletteInputRef = useRef<HTMLInputElement>(null);

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
        setPaletteOpen(true);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!paletteOpen) return;
    setPaletteIndex(0);
    setPaletteQuery("");
    const timer = window.setTimeout(() => paletteInputRef.current?.focus(), 0);
    return () => window.clearTimeout(timer);
  }, [paletteOpen]);

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

  const isDark = theme === "dark";

  const paletteActions: PaletteAction[] = useMemo(() => {
    const actions: PaletteAction[] = [
      {
        id: "refresh",
        label: "Refresh job list",
        shortcut: "R",
        run: () => loadRuns()
      },
      {
        id: "theme",
        label: isDark ? "Switch to light mode" : "Switch to dark mode",
        shortcut: "T",
        run: () => setTheme(isDark ? "light" : "dark")
      },
      {
        id: "focus-search",
        label: "Focus job search",
        shortcut: "S",
        run: () => searchInputRef.current?.focus()
      }
    ];

    if (query.trim()) {
      actions.push({
        id: "clear-search",
        label: "Clear job search",
        shortcut: "C",
        run: () => setQuery("")
      });
    }

    return actions;
  }, [isDark, query]);

  const filteredActions = useMemo(() => {
    const normalized = paletteQuery.trim().toLowerCase();
    if (!normalized) return paletteActions;
    return paletteActions.filter((action) =>
      action.label.toLowerCase().includes(normalized)
    );
  }, [paletteActions, paletteQuery]);

  useEffect(() => {
    if (!paletteOpen) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setPaletteOpen(false);
        return;
      }
      if (!filteredActions.length) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setPaletteIndex((index) => (index + 1) % filteredActions.length);
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setPaletteIndex((index) =>
          (index - 1 + filteredActions.length) % filteredActions.length
        );
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const action = filteredActions[paletteIndex];
        if (action) {
          action.run();
          setPaletteOpen(false);
          setPaletteQuery("");
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen, filteredActions, paletteIndex]);

  return (
    <div className="app-shell">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-plum dark:text-orange-300">Skedulord</p>
            <h1 className="font-display text-4xl font-semibold text-ink dark:text-slate-100">
              All jobs
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPaletteOpen(true)}
              className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
              aria-label="Open command palette"
            >
              <Command className="h-4 w-4" />
              Cmd + K
            </button>
            <button
              onClick={() => setTheme(isDark ? "light" : "dark")}
              className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 py-2 text-sm font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {isDark ? "Light" : "Dark"}
            </button>
            <button
              onClick={loadRuns}
              className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 py-2 text-sm font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </header>

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

          <div className="flex flex-col gap-2">
            <label
              className="text-xs font-semibold uppercase tracking-[0.2em] text-clay dark:text-slate-400"
              htmlFor="job-search"
            >
              Search jobs
            </label>
            <div className="flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/70 px-3 py-2 text-sm text-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100">
              <Search className="h-4 w-4 text-ink/40 dark:text-slate-400" />
              <input
                ref={searchInputRef}
                id="job-search"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Filter by job name"
                className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40 dark:placeholder:text-slate-400"
              />
            </div>
          </div>

          {error ? (
            <div className="flex items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          ) : null}

          <div className="overflow-hidden rounded-2xl border border-ink/5 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
            <ScrollArea.Root className="h-[520px]">
              <ScrollArea.Viewport className="p-2">
                <div className="flex flex-col gap-2">
                  {loading ? (
                    <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">Loading jobs...</p>
                  ) : null}
                  {!loading && filteredJobs.length === 0 ? (
                    <p className="px-4 py-6 text-sm text-ink/50 dark:text-slate-400">No jobs match this search.</p>
                  ) : null}
                  {filteredJobs.map((job) => (
                    <div
                      key={job.name}
                      className="rounded-2xl border border-transparent px-4 py-3 text-sm transition hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900/60"
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
                    </div>
                  ))}
                </div>
              </ScrollArea.Viewport>
              <ScrollArea.Scrollbar orientation="vertical" className="flex touch-none select-none p-1">
                <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/20 dark:bg-white/20" />
              </ScrollArea.Scrollbar>
            </ScrollArea.Root>
          </div>
        </section>
      </div>

      {paletteOpen ? (
        <div
          className="fixed inset-0 z-50 flex justify-center bg-black/30 px-4 py-20 backdrop-blur-sm dark:bg-black/60"
          onClick={() => {
            setPaletteOpen(false);
            setPaletteQuery("");
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
                ref={paletteInputRef}
                type="search"
                value={paletteQuery}
                onChange={(event) => {
                  setPaletteQuery(event.target.value);
                  setPaletteIndex(0);
                }}
                placeholder="Type a command"
                className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40 dark:placeholder:text-slate-400"
              />
              <span className="text-xs text-ink/40 dark:text-slate-400">Esc</span>
            </div>
            <div className="mt-3 max-h-64 overflow-auto" role="listbox">
              {filteredActions.length === 0 ? (
                <p className="px-3 py-4 text-sm text-ink/50 dark:text-slate-400">No matching commands.</p>
              ) : (
                filteredActions.map((action, index) => (
                  <button
                    key={action.id}
                    type="button"
                    onClick={() => {
                      action.run();
                      setPaletteOpen(false);
                      setPaletteQuery("");
                    }}
                    className={`flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                      index === paletteIndex
                        ? "bg-ink/5 text-ink dark:bg-white/10 dark:text-slate-100"
                        : "text-ink/70 hover:bg-ink/5 hover:text-ink dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-slate-100"
                    }`}
                    aria-selected={index === paletteIndex}
                    role="option"
                  >
                    <span>{action.label}</span>
                    {action.shortcut ? (
                      <span className="rounded-full border border-ink/10 px-2 py-0.5 text-xs text-ink/40 dark:border-white/10 dark:text-slate-400">
                        {action.shortcut}
                      </span>
                    ) : null}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
