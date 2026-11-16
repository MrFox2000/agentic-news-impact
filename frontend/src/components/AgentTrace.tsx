"use client";

import type { Step } from "@/lib/types";

const LABELS: Record<string, string> = {
  plan: "Planning",
  collect: "Calling MCP tools",
  report: "Writing report",
};

const ICONS: Record<string, string> = {
  plan: "◎",
  collect: "⛁",
  report: "✎",
};

export function AgentTrace({ steps, running }: { steps: Step[]; running: boolean }) {
  if (!steps.length && !running) {
    return (
      <div className="rounded-2xl border border-line bg-panel/60 p-5 text-sm text-zinc-400">
        The agent will plan, call its MCP tools, then write a report. Every step shows up here
        as it happens.
      </div>
    );
  }

  return (
    <ol className="space-y-3">
      {steps.map((step, index) => (
        <li
          key={`${step.node}-${index}`}
          className="rise flex gap-3 rounded-2xl border border-line bg-panel/60 p-4"
        >
          <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-accent/15 text-sm text-accent-soft">
            {ICONS[step.node] ?? "•"}
          </span>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              {LABELS[step.node] ?? step.node}
            </p>
            <p className="mt-0.5 text-sm leading-relaxed text-zinc-300">{step.detail}</p>
          </div>
        </li>
      ))}

      {running ? (
        <li className="flex items-center gap-3 rounded-2xl border border-dashed border-line bg-panel/30 p-4 text-sm text-zinc-500">
          <span className="flex size-7 items-center justify-center">
            <span className="size-3 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
          </span>
          working…
        </li>
      ) : null}
    </ol>
  );
}
