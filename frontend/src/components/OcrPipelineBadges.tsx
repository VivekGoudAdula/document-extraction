"use client";

import type { PipelineStatus } from "@/types/extraction";

interface OcrPipelineBadgesProps {
  pipeline?: PipelineStatus;
}

function Badge({
  label,
  active,
  variant,
}: {
  label: string;
  active: boolean;
  variant: "paddle" | "trocr" | "neutral";
}) {
  const colors = {
    paddle: active
      ? "bg-sky-50 text-sky-800 ring-sky-200"
      : "bg-slate-50 text-slate-400 ring-slate-200",
    trocr: active
      ? "bg-violet-50 text-violet-800 ring-violet-200"
      : "bg-slate-50 text-slate-400 ring-slate-200",
    neutral: active
      ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
      : "bg-slate-50 text-slate-400 ring-slate-200",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${colors[variant]}`}
    >
      {label}
    </span>
  );
}

export function OcrPipelineBadges({ pipeline }: OcrPipelineBadgesProps) {
  if (!pipeline) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge
        label="OpenCV"
        active={pipeline.preprocessing}
        variant="neutral"
      />
      {pipeline.ocr_execution_mode === "local" && (
        <Badge label="Local OCR" active variant="neutral" />
      )}
      <Badge
        label="PaddleOCR"
        active={pipeline.paddleocr_success}
        variant="paddle"
      />
      <Badge label="TrOCR" active={pipeline.trocr_success} variant="trocr" />
    </div>
  );
}
