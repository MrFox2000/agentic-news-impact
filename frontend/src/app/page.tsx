"use client";

import { useCallback, useState } from "react";

import { AgentTrace } from "@/components/AgentTrace";
import { Markdown } from "@/components/Markdown";
import { runAnalysis } from "@/lib/api";
import type { Step } from "@/lib/types";

const WINDOWS = [30, 60, 90];

export default function Home() {
  const [symbol, setSymbol] = useState("AAPL");
  const [question, setQuestion] = useState("");
  const [days, setDays] = useState(30);
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [report, setReport] = useState("");
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async () => {
    const ticker = symbol.trim().toUpperCase();
    if (!ticker || running) return;

    setRunning(true);
    setSteps([]);
    setReport("");
    setError(null);

    try {
      await runAnalysis(ticker, question.trim(), days, {
        onStep: (step) => setSteps((previous) => [...previous, step]),
        onReport: (markdown) => setReport(markdown),
        onError: (message) => setError(message),
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analysis failed");
    } finally {
      setRunning(false);
    }
  }, [days, question, running, symbol]);

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-6xl flex-col px-4 py-6 sm:px-6">
      <header className="flex flex-wrap items-center justify-between gap-4 pb-6">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl bg-accent/15 text-accent-soft">
            <svg viewBox="0 0 24 24" fill="none" className="size-5" aria-hidden>
              <path
                d="M4 16.5 9 11l3.5 3.5L20 7"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M20 11V7h-4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-white">News → Price Impact</h1>
            <p className="text-xs text-zinc-500">An MCP agent that connects headlines to moves</p>
          </div>
        </div>

        <span className="rounded-full border border-line bg-panel px-3 py-1 text-[11px] text-zinc-400">
          LangGraph · MCP · FastAPI
        </span>
      </header>

      <section className="rounded-2xl border border-line bg-panel/50 p-4 sm:p-5">
        <form
          className="flex flex-col gap-3 sm:flex-row sm:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            void run();
          }}
        >
          <label className="flex flex-col gap-1">
            <span className="text-[11px] uppercase tracking-wider text-zinc-500">Ticker</span>
            <input
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="AAPL or BTC-USD"
              className="w-40 rounded-lg border border-line bg-surface px-3 py-2 text-sm text-zinc-100 outline-none focus:border-accent/70"
            />
          </label>

          <label className="flex min-w-0 flex-1 flex-col gap-1">
            <span className="text-[11px] uppercase tracking-wider text-zinc-500">
              Focus (optional)
            </span>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="e.g. supply chain, regulation, earnings"
              className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-zinc-100 outline-none focus:border-accent/70"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-[11px] uppercase tracking-wider text-zinc-500">Window</span>
            <select
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
              className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-zinc-100 outline-none focus:border-accent/70"
            >
              {WINDOWS.map((option) => (
                <option key={option} value={option}>
                  {option} days
                </option>
              ))}
            </select>
          </label>

          <button
            type="submit"
            disabled={running || !symbol.trim()}
            className="h-[38px] rounded-lg bg-accent px-5 text-sm font-medium text-white transition hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? "Running…" : "Analyse"}
          </button>
        </form>

        {error ? (
          <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        ) : null}
      </section>

      <div className="mt-5 grid min-h-0 flex-1 gap-5 lg:grid-cols-[minmax(0,340px)_minmax(0,1fr)]">
        <section className="min-w-0">
          <h2 className="mb-3 text-[11px] uppercase tracking-wider text-zinc-500">Agent trace</h2>
          <AgentTrace steps={steps} running={running} />
        </section>

        <section className="min-w-0">
          <h2 className="mb-3 text-[11px] uppercase tracking-wider text-zinc-500">Report</h2>
          <div className="rounded-2xl border border-line bg-panel/60 p-5">
            {report ? (
              <Markdown source={report} />
            ) : (
              <p className="text-sm text-zinc-500">
                The report appears here once the agent has collected the data. Try{" "}
                <span className="text-zinc-300">AAPL</span> or{" "}
                <span className="text-zinc-300">BTC-USD</span>.
              </p>
            )}
          </div>
        </section>
      </div>

      <footer className="pt-5 text-center text-[11px] text-zinc-600">
        Headlines from Google News · prices from Yahoo Finance · correlation, not causation
      </footer>
    </main>
  );
}
