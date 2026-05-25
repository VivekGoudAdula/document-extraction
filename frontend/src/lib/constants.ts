import {
  PRODUCTION_BACKEND_URL,
  PRODUCTION_FRONTEND_URL,
} from "@/lib/deploy-urls";

export { PRODUCTION_BACKEND_URL, PRODUCTION_FRONTEND_URL };

/** /extract hits Render directly (OCR can take many minutes). */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? PRODUCTION_BACKEND_URL
).replace(/\/+$/, "");

/**
 * Health: same-origin rewrite on Vercel (next.config.ts → Render /health).
 * /extract stays cross-origin to Render with CORS on the API.
 */
export const HEALTH_CHECK_URL = API_BASE_URL.includes("onrender.com")
  ? "/api/health"
  : `${API_BASE_URL}/health`;

export const ACCEPTED_FILE_TYPES = [
  "image/png",
  "image/jpeg",
  "image/jpg",
  "image/webp",
] as const;

export const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"] as const;

export const MAX_FILE_SIZE_MB = 25;

export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
