import { NextResponse } from "next/server";

import { PRODUCTION_BACKEND_URL } from "@/lib/deploy-urls";

export const dynamic = "force-dynamic";

function backendUrl(): string {
  const url =
    process.env.BACKEND_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    PRODUCTION_BACKEND_URL;
  return url.replace(/\/+$/, "");
}

/** Same-origin health check — wakes Render without browser CORS. */
export async function GET() {
  try {
    const res = await fetch(`${backendUrl()}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(55_000),
    });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { status: "unreachable", detail: "Backend not responding" },
      { status: 502 },
    );
  }
}
