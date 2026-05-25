"use client";

import dynamic from "next/dynamic";

const ExtractionWorkspace = dynamic(
  () =>
    import("@/components/ExtractionWorkspace").then(
      (mod) => mod.ExtractionWorkspace,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="mx-auto flex max-w-7xl items-center justify-center px-4 py-24">
        <p className="text-sm text-slate-500">Loading workspace…</p>
      </div>
    ),
  },
);

export function HomePage() {
  return <ExtractionWorkspace />;
}
