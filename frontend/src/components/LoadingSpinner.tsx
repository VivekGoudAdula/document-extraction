interface LoadingSpinnerProps {
  label?: string;
  sublabel?: string;
  overlay?: boolean;
}

export function LoadingSpinner({
  label = "Running Local OCR…",
  sublabel,
  overlay = false,
}: LoadingSpinnerProps) {
  const content = (
    <div className="flex flex-col items-center gap-4 text-center">
      <div
        className="h-12 w-12 animate-spin rounded-full border-[3px] border-slate-200 border-t-blue-600"
        role="status"
        aria-label="Loading"
      />
      <div>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {sublabel && (
          <p className="mt-1 text-xs text-slate-500">{sublabel}</p>
        )}
      </div>
    </div>
  );

  if (overlay) {
    return (
      <div className="absolute inset-0 z-20 flex items-center justify-center rounded-2xl bg-white/80 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
}
