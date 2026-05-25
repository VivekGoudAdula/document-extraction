"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { extractDocument, getApiErrorMessage } from "@/lib/api";
import type { ExtractionResponse, JsonValue } from "@/types/extraction";

import { ExtractionResult } from "./ExtractionResult";
import { FilePreview } from "./FilePreview";
import { JsonViewer } from "./JsonViewer";
import { LoadingSpinner } from "./LoadingSpinner";
import { OcrPipelineBadges } from "./OcrPipelineBadges";
import { UploadZone } from "./UploadZone";

const PROMPT_PLACEHOLDER =
  "Extract all key fields as JSON, e.g. invoice_number, date, total — or ask: What is the main topic of this document?";

type ResultView = "formatted" | "json";

export function ExtractionWorkspace() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [resultView, setResultView] = useState<ResultView>("formatted");

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileSelect = useCallback((selected: File) => {
    setResult(null);
    setFile(selected);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(selected);
    });
    toast.success("Image ready for extraction");
  }, []);

  const handleRemoveFile = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    toast.info("Image removed");
  }, [previewUrl]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!file) {
      toast.error("Please upload an image first.");
      return;
    }

    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      toast.error("Please enter an extraction prompt.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await extractDocument(file, trimmedPrompt);
      setResult(response);
      toast.success("Extraction complete");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const aiData = result?.ai_response as JsonValue | undefined;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Secure local-OCR document extraction
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-600 sm:text-base">
          Upload a scanned image, form, screenshot, or handwritten note. OpenCV,
          PaddleOCR, and TrOCR run locally on our server; only GPT-4o semantic
          extraction uses an external API.
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <section className="relative space-y-6">
          {loading && (
            <LoadingSpinner
              overlay
              label="Running Local OCR…"
              sublabel="First request on cloud may take 2–5 min while OCR models load"
            />
          )}

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
              1. Upload image
            </h3>

            {!file ? (
              <UploadZone
                onFileSelect={handleFileSelect}
                onValidationError={(msg) => toast.error(msg)}
                disabled={loading}
              />
            ) : (
              <FilePreview
                file={file}
                previewUrl={previewUrl}
                onRemove={handleRemoveFile}
              />
            )}
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
          >
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
              2. Extraction prompt
            </h3>

            <label htmlFor="extraction-prompt" className="sr-only">
              Extraction prompt
            </label>
            <textarea
              id="extraction-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={PROMPT_PLACEHOLDER}
              rows={5}
              disabled={loading}
              className="w-full resize-y rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-60"
            />

            <button
              type="submit"
              disabled={loading || !file}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none sm:w-auto sm:min-w-[200px]"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Running Local OCR…
                </>
              ) : (
                "Run extraction"
              )}
            </button>
          </form>
        </section>

        <section className="flex min-h-[400px] flex-col">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              3. Results
            </h3>
            <div className="flex flex-wrap items-center gap-2">
              {result?.pipeline && (
                <OcrPipelineBadges pipeline={result.pipeline} />
              )}
              {result && (
                <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                  Complete
                </span>
              )}
            </div>
          </div>

          {loading && !result && (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-slate-200 bg-white p-12">
              <LoadingSpinner
                label="Running Local OCR…"
                sublabel="Processing using PaddleOCR + TrOCR — OCR inference running locally"
              />
            </div>
          )}

          {!loading && !result && (
            <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-12 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
                <svg
                  className="h-7 w-7"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  aria-hidden
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"
                  />
                </svg>
              </div>
              <p className="text-sm font-medium text-slate-600">
                Structured JSON will appear here
              </p>
              <p className="mt-1 max-w-xs text-xs text-slate-400">
                Upload an image, enter your prompt, and submit.
              </p>
            </div>
          )}

          {result && aiData !== undefined && (
            <div className="flex min-h-0 flex-1 flex-col gap-3">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setResultView("formatted")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                    resultView === "formatted"
                      ? "bg-blue-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  Formatted
                </button>
                <button
                  type="button"
                  onClick={() => setResultView("json")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                    resultView === "json"
                      ? "bg-blue-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  JSON
                </button>
              </div>
              <div className="min-h-0 flex-1">
                {resultView === "json" ? (
                  <JsonViewer data={aiData} title="Extraction result" />
                ) : (
                  <ExtractionResult data={aiData} />
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
