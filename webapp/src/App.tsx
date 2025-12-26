import { useEffect, useMemo, useState } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import * as Tabs from "@radix-ui/react-tabs";
import { AlertCircle, Moon, RefreshCw, Sun } from "lucide-react";

import { fetchLog, fetchRuns, type RunEntry } from "./api";

function StatusPill({ status }: { status: string }) {
  const color = status === "success" ? "bg-emerald-500" : status === "fail" ? "bg-rose-500" : "bg-slate-400";
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-ink shadow-sm dark:bg-slate-900/70 dark:text-slate-100">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {status}
    </span>
  );
}

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const stored = window.localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const [runs, setRuns] = useState<RunEntry[]>([]);
  const [selected, setSelected] = useState<RunEntry | null>(null);
  const [logContent, setLogContent] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<"all" | "success" | "fail">("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRuns({
        limit: 100,
        name: query || undefined,
        status: statusFilter === "all" ? undefined : statusFilter
      });
      setRuns(data);
      setSelected((current) => current ?? data[0] ?? null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRuns();
  }, [statusFilter]);

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
    if (!selected) return;
    fetchLog(selected.id)
      .then((data) => setLogContent(data.content))
      .catch(() => setLogContent("Unable to load log content."));
  }, [selected]);

  const stats = useMemo(() => {
    const total = runs.length;
    const failures = runs.filter((run) => run.status === "fail").length;
    const successes = runs.filter((run) => run.status === "success").length;
    return { total, failures, successes };
  }, [runs]);
  const isDark = theme === "dark";

  return (
    <div className="app-shell">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-plum dark:text-orange-300">Skedulord</p>
              <h1 className="font-display text-4xl font-semibold text-ink dark:text-slate-100">Runboard</h1>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setTheme(isDark ? "light" : "dark")}
                className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 py-2 text-sm font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
                aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              >
                {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                {isDark ? "Light mode" : "Dark mode"}
              </button>
              <button
                onClick={loadRuns}
                className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white/80 px-4 py-2 text-sm font-medium text-ink shadow-sm transition hover:-translate-y-0.5 hover:shadow-card dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            </div>
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="frost-card rounded-2xl p-5 shadow-card">
              <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Runs tracked</p>
              <p className="mt-2 font-display text-3xl text-ink dark:text-slate-100">{stats.total}</p>
              <p className="mt-1 text-sm text-ink/60 dark:text-slate-300">Latest 100 runs in view</p>
            </div>
            <div className="frost-card rounded-2xl p-5 shadow-card">
              <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Healthy</p>
              <p className="mt-2 font-display text-3xl text-ink dark:text-slate-100">{stats.successes}</p>
              <p className="mt-1 text-sm text-ink/60 dark:text-slate-300">Successful executions</p>
            </div>
            <div className="frost-card rounded-2xl p-5 shadow-card">
              <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Needs attention</p>
              <p className="mt-2 font-display text-3xl text-ink dark:text-slate-100">{stats.failures}</p>
              <p className="mt-1 text-sm text-ink/60 dark:text-slate-300">Failures in this view</p>
            </div>
          </div>
        </header>

        <Tabs.Root defaultValue="runs" className="flex flex-1 flex-col gap-6">
          <Tabs.List className="flex flex-wrap gap-3">
            {["runs", "activity", "settings"].map((tab) => (
              <Tabs.Trigger
                key={tab}
                value={tab}
                className="rounded-full border border-transparent bg-white/70 px-4 py-2 text-sm font-medium text-ink transition data-[state=active]:border-ink/10 data-[state=active]:bg-white data-[state=active]:shadow-sm dark:bg-slate-900/70 dark:text-slate-100 dark:data-[state=active]:border-white/10 dark:data-[state=active]:bg-slate-900"
              >
                {tab}
              </Tabs.Trigger>
            ))}
          </Tabs.List>

          <Tabs.Content value="runs" className="flex flex-1 flex-col gap-6">
            <div className="grid gap-6 lg:grid-cols-[1.1fr_2fr]">
              <div className="frost-card flex flex-col gap-4 rounded-3xl p-5 shadow-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Run archive</p>
                    <h2 className="font-display text-2xl">Recent jobs</h2>
                  </div>
                  <div className="flex gap-2 rounded-full bg-white/80 p-1 text-xs dark:bg-slate-900/70">
                    {(["all", "success", "fail"] as const).map((status) => (
                      <button
                        key={status}
                        onClick={() => setStatusFilter(status)}
                        className={`rounded-full px-3 py-1 font-medium transition ${
                          statusFilter === status
                            ? "bg-ink text-white dark:bg-orange-400 dark:text-slate-900"
                            : "text-ink/60 hover:text-ink dark:text-slate-300 dark:hover:text-slate-100"
                        }`}
                      >
                        {status}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Filter by job name"
                    className="w-full rounded-2xl border border-ink/10 bg-white/70 px-4 py-2 text-sm outline-none focus:border-ink/30 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-100 dark:placeholder:text-slate-400 dark:focus:border-white/20"
                  />
                  <button
                    onClick={loadRuns}
                    className="rounded-2xl border border-ink/10 bg-ink px-4 py-2 text-sm font-semibold text-white dark:border-white/10 dark:bg-orange-400 dark:text-slate-900"
                  >
                    Go
                  </button>
                </div>

                <div className="flex-1 overflow-hidden rounded-2xl border border-ink/5 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
                  <ScrollArea.Root className="h-[420px]">
                    <ScrollArea.Viewport className="p-2">
                      <div className="flex flex-col gap-2">
                        {runs.map((run) => (
                          <button
                            key={run.id}
                            onClick={() => setSelected(run)}
                            className={`rounded-2xl border px-4 py-3 text-left text-sm transition ${
                              selected?.id === run.id
                                ? "border-ink/20 bg-white shadow-soft dark:border-white/10 dark:bg-slate-900"
                                : "border-transparent hover:border-ink/10 hover:bg-white dark:hover:border-white/10 dark:hover:bg-slate-900/60"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div>
                                <p className="font-medium text-ink dark:text-slate-100">{run.name}</p>
                                <p className="text-xs text-ink/50 dark:text-slate-400">{run.start}</p>
                              </div>
                              <StatusPill status={run.status} />
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
              </div>

              <div className="frost-card flex flex-col gap-4 rounded-3xl p-6 shadow-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-clay dark:text-slate-400">Log viewer</p>
                    <h2 className="font-display text-2xl">{selected?.name ?? "Select a run"}</h2>
                  </div>
                  {selected ? <StatusPill status={selected.status} /> : null}
                </div>

                {error ? (
                  <div className="flex items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                  </div>
                ) : null}

                <div className="rounded-2xl border border-ink/10 bg-ink px-4 py-3 text-xs text-white/70 dark:border-white/10 dark:bg-slate-950 dark:text-slate-300">
                  <p className="text-white/90 dark:text-slate-100">{selected?.command ?? "No command selected"}</p>
                </div>

                <div className="flex-1 overflow-hidden rounded-2xl border border-ink/5 bg-white/80 dark:border-white/10 dark:bg-slate-900/70">
                  <ScrollArea.Root className="h-[420px]">
                    <ScrollArea.Viewport className="p-4">
                      <pre className="whitespace-pre-wrap text-xs leading-relaxed text-ink/80 dark:text-slate-200">
                        {logContent || (loading ? "Loading..." : "Select a run to view logs.")}
                      </pre>
                    </ScrollArea.Viewport>
                    <ScrollArea.Scrollbar orientation="vertical" className="flex touch-none select-none p-1">
                      <ScrollArea.Thumb className="relative flex-1 rounded-full bg-ink/20 dark:bg-white/20" />
                    </ScrollArea.Scrollbar>
                  </ScrollArea.Root>
                </div>
              </div>
            </div>
          </Tabs.Content>

          <Tabs.Content value="activity" className="frost-card rounded-3xl p-6 shadow-card">
            <h2 className="font-display text-2xl">Activity stream</h2>
            <p className="mt-2 text-sm text-ink/60 dark:text-slate-300">
              Timeline and alerting hooks can live here once we add more metadata.
            </p>
          </Tabs.Content>

          <Tabs.Content value="settings" className="frost-card rounded-3xl p-6 shadow-card">
            <h2 className="font-display text-2xl">Workspace settings</h2>
            <p className="mt-2 text-sm text-ink/60 dark:text-slate-300">
              Configure retention, scheduling, and API auth here once we wire up the backend.
            </p>
          </Tabs.Content>
        </Tabs.Root>
      </div>
    </div>
  );
}
