"use client";

import { formatFileSize } from "@/lib/file-validation";

interface FilePreviewProps {
  file: File;
  previewUrl: string | null;
  onRemove: () => void;
}

export function FilePreview({ file, previewUrl, onRemove }: FilePreviewProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-800">{file.name}</p>
          <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="ml-3 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-200 hover:text-slate-900"
        >
          Remove
        </button>
      </div>

      <div className="relative flex min-h-[220px] items-center justify-center bg-slate-100 p-4 sm:min-h-[280px]">
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewUrl}
            alt={`Preview of ${file.name}`}
            className="max-h-[320px] max-w-full rounded-lg object-contain shadow-md"
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-slate-500">
            <svg
              className="h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
              aria-hidden
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
            <p className="text-sm font-medium">Preview unavailable</p>
          </div>
        )}
      </div>
    </div>
  );
}
