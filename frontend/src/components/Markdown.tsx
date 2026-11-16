"use client";

import { Fragment, type ReactNode } from "react";

/** Renders the small markdown subset the agent emits. No dependencies. */

const LINK = /\[([^\]]+)\]\(([^)]+)\)/g;
const BOLD = /\*\*([^*]+)\*\*/g;

function inline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let cursor = 0;
  let match: RegExpExecArray | null;
  LINK.lastIndex = 0;

  while ((match = LINK.exec(text)) !== null) {
    if (match.index > cursor) nodes.push(renderBold(text.slice(cursor, match.index), `${keyPrefix}-t${match.index}`));
    nodes.push(
      <a
        key={`${keyPrefix}-a${match.index}`}
        href={match[2]}
        target="_blank"
        rel="noreferrer noopener"
        className="text-accent-soft underline decoration-accent/40 underline-offset-2 hover:text-white"
      >
        {match[1]}
      </a>,
    );
    cursor = match.index + match[0].length;
  }
  if (cursor < text.length) nodes.push(renderBold(text.slice(cursor), `${keyPrefix}-tail`));
  return nodes;
}

function renderBold(text: string, keyPrefix: string): ReactNode {
  const parts = text.split(BOLD);
  return (
    <Fragment key={keyPrefix}>
      {parts.map((part, index) =>
        index % 2 === 1 ? (
          <strong key={index} className="font-semibold text-white">
            {part}
          </strong>
        ) : (
          <Fragment key={index}>{part}</Fragment>
        ),
      )}
    </Fragment>
  );
}

export function Markdown({ source }: { source: string }) {
  const blocks: ReactNode[] = [];
  let list: string[] = [];

  const flush = () => {
    if (!list.length) return;
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="my-3 space-y-1.5 pl-1">
        {list.map((item, index) => (
          <li key={index} className="flex gap-2 text-sm text-zinc-300">
            <span className="mt-2 size-1 shrink-0 rounded-full bg-accent-soft" />
            <span>{inline(item, `li-${blocks.length}-${index}`)}</span>
          </li>
        ))}
      </ul>,
    );
    list = [];
  };

  source.split("\n").forEach((raw, index) => {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flush();
      return;
    }
    if (line.startsWith("- ")) {
      list.push(line.slice(2));
      return;
    }
    flush();
    if (line.startsWith("### ")) {
      blocks.push(
        <h4 key={index} className="mt-5 mb-1 text-sm font-semibold text-white">
          {inline(line.slice(4), `h4-${index}`)}
        </h4>,
      );
    } else if (line.startsWith("## ")) {
      blocks.push(
        <h3 key={index} className="mt-6 mb-2 text-base font-semibold text-white first:mt-0">
          {inline(line.slice(3), `h3-${index}`)}
        </h3>,
      );
    } else if (line.startsWith("> ")) {
      blocks.push(
        <blockquote
          key={index}
          className="my-4 border-l-2 border-accent/50 pl-3 text-sm italic text-zinc-400"
        >
          {inline(line.slice(2), `bq-${index}`)}
        </blockquote>,
      );
    } else {
      blocks.push(
        <p key={index} className="my-2 text-sm leading-relaxed text-zinc-300">
          {inline(line, `p-${index}`)}
        </p>,
      );
    }
  });
  flush();

  return <div>{blocks}</div>;
}
