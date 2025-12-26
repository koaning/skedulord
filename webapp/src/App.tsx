import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import { AlertCircle, CornerUpLeft, Moon, RefreshCw, Search, Sun } from "lucide-react";

import { fetchRuns, type RunEntry } from "./api";

const MAX_RECENT_RUNS = 20;
const RUNS_PER_PAGE = 25;
const SUGGESTION_LIMIT = 8;

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
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [isFocused, setIsFocused] = useState(false);

  const commandInputRef = useRef<HTMLInputElement>(null);

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
        commandInputRef.current?.focus();
        commandInputRef.current?.select();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

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
    setPage(0);
  }, [selectedJob]);

  const isDark = theme === "dark";

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
        shortcut: "T",
        run: () => setTheme(isDark ? "light" : "dark")
      }
    ];

    if (selectedJob) {
      actions.push({
        id: "back",
        label: "Back to all jobs",
        type: "action",
        shortcut: "B",
        run: () => setSelectedJob(null)
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
  }, [isDark, query, selectedJob]);

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
      return;
    }
    setSelectedJob(item.jobName);
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
    }
  }

  const pageCount = selectedJobData
    ? Math.max(1, Math.ceil(selectedJobData.runs.length / RUNS_PER_PAGE))
    : 1;
  const pageRuns = selectedJobData
    ? selectedJobData.runs.slice(page * RUNS_PER_PAGE, (page + 1) * RUNS_PER_PAGE)
    : [];

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
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Command bar</p>
            <div className="mt-2 flex items-center gap-3 rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm text-ink shadow-sm dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100">
              <Search className="h-4 w-4 text-ink/40 dark:text-slate-400" />
              <input
                ref={commandInputRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleCommandKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder="Type a command or job name…"
                className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40 dark:placeholder:text-slate-400"
                role="combobox"
                aria-expanded={isFocused || query.length > 0}
                aria-controls="command-suggestions"
              />
              <span className="text-xs text-ink/40 dark:text-slate-400">⌘K</span>
            </div>
            {(isFocused || query.length > 0) && suggestionItems.length > 0 ? (
              <div
                id="command-suggestions"
                role="listbox"
                className="mt-3 grid gap-2 rounded-2xl border border-ink/10 bg-white/80 p-3 text-sm shadow-soft dark:border-white/10 dark:bg-slate-950/80"
              >
                {suggestionItems.map((item, index) => (
                  <button
                    key={item.id}
                    type="button"
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => handleSuggestionSelect(item)}
                    className={`flex items-center justify-between rounded-xl px-3 py-2 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:focus-visible:outline-slate-100 ${
                      index === highlightIndex
                        ? "bg-ink/5 text-ink dark:bg-white/10 dark:text-slate-100"
                        : "text-ink/70 hover:bg-ink/5 hover:text-ink dark:text-slate-300 dark:hover:bg-white/10 dark:hover:text-slate-100"
                    }`}
                    role="option"
                    aria-selected={index === highlightIndex}
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
                ))}
              </div>
            ) : null}
          </div>
        </section>

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
                  onClick={() => setSelectedJob(null)}
                  className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-3 py-2 text-xs font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                >
                  <CornerUpLeft className="h-3 w-3" />
                  Back
                </button>
                {selectedJobData.latest ? <StatusPill status={selectedJobData.latest.status} /> : null}
              </div>
            </div>

            <div className="rounded-2xl border border-ink/10 bg-white/80 p-4 dark:border-white/10 dark:bg-slate-900/70">
              <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                <p className="font-semibold text-ink dark:text-slate-100">Recent run durations</p>
                <p className="text-xs text-ink/60 dark:text-slate-300">Last {MAX_RECENT_RUNS} runs</p>
              </div>
              <div className="mt-4">
                <RunBars runs={selectedJobData.runs} />
              </div>
            </div>

            <div className="rounded-2xl border border-ink/10 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/5 px-4 py-3 text-xs uppercase tracking-[0.2em] text-clay dark:border-white/10 dark:text-slate-400">
                <span>Runs</span>
                <span>
                  Page {page + 1} of {pageCount}
                </span>
              </div>
              <ScrollArea.Root className="h-[420px]">
                <ScrollArea.Viewport className="p-2">
                  <div className="flex flex-col gap-2">
                    {pageRuns.map((run) => (
                      <div
                        key={run.id}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-transparent px-4 py-3 text-sm transition hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900"
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
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea.Viewport>
                <ScrollArea.Scrollbar orientation="vertical" className="flex touch-none select-none p-1">
                  <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/20 dark:bg-white/20" />
                </ScrollArea.Scrollbar>
              </ScrollArea.Root>
              <div className="flex items-center justify-between border-t border-ink/5 px-4 py-3 text-sm dark:border-white/10">
                <button
                  type="button"
                  onClick={() => setPage((current) => Math.max(0, current - 1))}
                  disabled={page === 0}
                  className="rounded-full border border-ink/10 px-3 py-1 text-xs font-semibold text-ink transition disabled:opacity-40 dark:border-white/10 dark:text-slate-100"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
                  disabled={page + 1 >= pageCount}
                  className="rounded-full border border-ink/10 px-3 py-1 text-xs font-semibold text-ink transition disabled:opacity-40 dark:border-white/10 dark:text-slate-100"
                >
                  Next
                </button>
              </div>
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
                      <button
                        key={job.name}
                        type="button"
                        onClick={() => setSelectedJob(job.name)}
                        className="rounded-2xl border border-transparent px-4 py-3 text-left text-sm transition hover:border-ink/10 hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink dark:hover:border-white/10 dark:hover:bg-slate-900/60 dark:focus-visible:outline-slate-100"
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
    </div>
  );
}
