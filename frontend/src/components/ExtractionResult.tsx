"use client";

import { useState } from "react";

import {
  formatDisplayAsPlainText,
  getDisplayContent,
} from "@/lib/format-result";
import type { JsonValue } from "@/types/extraction";

import { FormattedValue } from "./FormattedValue";

interface ExtractionResultProps {
  data: JsonValue;
}

export function ExtractionResult({ data }: ExtractionResultProps) {
  const [copied, setCopied] = useState(false);
  const content = getDisplayContent(data);
  const plainText = formatDisplayAsPlainText(content);

  const jsonText = JSON.stringify(data, null, 2);

  const handleCopy = async () => {
    const text = jsonText || plainText;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Results</h3>
        {(plainText || jsonText) && (
          <button
            type="button"
            onClick={handleCopy}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:border-blue-300 hover:text-blue-700"
          >
            {copied ? "Copied!" : "Copy JSON"}
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto p-5 sm:p-6">
        {content.mode === "empty" && (
          <p className="text-sm text-slate-500">No content returned.</p>
        )}

        {content.mode === "answer" && (
          <div className="space-y-4">
            {content.question && (
              <p className="text-sm text-slate-500">
                <span className="font-medium text-slate-600">Question: </span>
                {content.question}
              </p>
            )}
            <p className="text-base leading-relaxed text-slate-800 sm:text-lg">
              {content.answer}
            </p>
          </div>
        )}

        {content.mode === "fields" && (
          <div className="space-y-6">
            {content.question && (
              <p className="border-b border-slate-100 pb-4 text-sm text-slate-500">
                <span className="font-medium text-slate-600">Question: </span>
                {content.question}
              </p>
            )}
            {content.items.map(({ label, value }) => (
              <section key={label}>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {label}
                </h4>
                <FormattedValue value={value} />
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
