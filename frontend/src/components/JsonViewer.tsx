"use client";

import { useMemo, useState } from "react";

import type { JsonValue } from "@/types/extraction";

interface JsonViewerProps {
  data: JsonValue;
  title?: string;
}

function JsonNode({ value, depth = 0 }: { value: JsonValue; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);

  if (value === null) {
    return <span className="text-slate-400">null</span>;
  }

  if (typeof value === "boolean") {
    return <span className="text-amber-600">{String(value)}</span>;
  }

  if (typeof value === "number") {
    return <span className="text-emerald-600">{value}</span>;
  }

  if (typeof value === "string") {
    return <span className="text-blue-700">&quot;{value}&quot;</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-slate-500">[]</span>;
    }

    return (
      <div className="inline-block align-top">
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="mr-1 rounded px-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          aria-expanded={expanded}
        >
          {expanded ? "▼" : "▶"}
        </button>
        <span className="text-slate-500">[</span>
        {expanded ? (
          <div className="ml-4 border-l border-slate-200 pl-3">
            {value.map((item, index) => (
              <div key={index} className="py-0.5">
                <JsonNode value={item as JsonValue} depth={depth + 1} />
                {index < value.length - 1 && (
                  <span className="text-slate-400">,</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <span className="mx-1 text-xs text-slate-400">{value.length} items</span>
        )}
        <span className="text-slate-500">]</span>
      </div>
    );
  }

  const entries = Object.entries(value);
  if (entries.length === 0) {
    return <span className="text-slate-500">{`{}`}</span>;
  }

  return (
    <div className="inline-block align-top">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="mr-1 rounded px-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        aria-expanded={expanded}
      >
        {expanded ? "▼" : "▶"}
      </button>
      <span className="text-slate-500">{`{`}</span>
      {expanded ? (
        <div className="ml-4 border-l border-slate-200 pl-3">
          {entries.map(([key, child], index) => (
            <div key={key} className="py-0.5 font-mono text-sm">
              <span className="text-violet-700">&quot;{key}&quot;</span>
              <span className="text-slate-400">: </span>
              <JsonNode value={child as JsonValue} depth={depth + 1} />
              {index < entries.length - 1 && (
                <span className="text-slate-400">,</span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <span className="mx-1 text-xs text-slate-400">
          {entries.length} keys
        </span>
      )}
      <span className="text-slate-500">{`}`}</span>
    </div>
  );
}

export function JsonViewer({ data, title = "Extracted data" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);
  const formatted = useMemo(() => JSON.stringify(data, null, 2), [data]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(formatted);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
          <p className="text-xs text-slate-500">Structured AI response</p>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:border-blue-300 hover:text-blue-700"
        >
          {copied ? "Copied!" : "Copy JSON"}
        </button>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <div className="rounded-xl bg-slate-950 p-4 font-mono text-sm leading-relaxed text-slate-100">
          <JsonNode value={data} />
        </div>
      </div>

      <details className="border-t border-slate-100">
        <summary className="cursor-pointer px-4 py-2.5 text-xs font-medium text-slate-500 hover:text-slate-700">
          View raw JSON
        </summary>
        <pre className="max-h-48 overflow-auto border-t border-slate-100 bg-slate-50 p-4 text-xs text-slate-700">
          {formatted}
        </pre>
      </details>
    </div>
  );
}
