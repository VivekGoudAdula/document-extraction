"use client";

import { useCallback, useRef, useState } from "react";

import { validateFile } from "@/lib/file-validation";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  onValidationError?: (message: string) => void;
  disabled?: boolean;
}

export function UploadZone({
  onFileSelect,
  onValidationError,
  disabled = false,
}: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file || disabled) return;

      const error = validateFile(file);
      if (error) {
        onValidationError?.(error);
        return;
      }
      onFileSelect(file);
    },
    [disabled, onFileSelect, onValidationError],
  );

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      handleFile(event.dataTransfer.files[0]);
    },
    [disabled, handleFile],
  );

  return (
    <div
      onDragEnter={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setIsDragging(false);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      className={`relative rounded-2xl border-2 border-dashed transition-all ${
        isDragging
          ? "border-blue-500 bg-blue-50/60"
          : "border-slate-300 bg-slate-50/50 hover:border-blue-400 hover:bg-blue-50/30"
      } ${disabled ? "pointer-events-none opacity-60" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
        className="sr-only"
        disabled={disabled}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        className="flex w-full flex-col items-center gap-4 px-6 py-10 text-center"
      >
        <div
          className={`flex h-14 w-14 items-center justify-center rounded-2xl ${
            isDragging ? "bg-blue-100 text-blue-600" : "bg-white text-slate-500 shadow-sm"
          }`}
        >
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
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
        </div>

        <div>
          <p className="text-base font-semibold text-slate-800">
            {isDragging ? "Drop your image here" : "Drag & drop your image"}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            or{" "}
            <span className="font-medium text-blue-600">browse files</span> — PNG,
            JPG, JPEG, WEBP
          </p>
        </div>
      </button>
    </div>
  );
}
