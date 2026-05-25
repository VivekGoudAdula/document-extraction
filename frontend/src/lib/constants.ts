import {
  PRODUCTION_BACKEND_URL,
  PRODUCTION_FRONTEND_URL,
} from "@/lib/deploy-urls";

export { PRODUCTION_BACKEND_URL, PRODUCTION_FRONTEND_URL };

/** Direct Render API (long /extract must hit backend — not Vercel serverless). */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? PRODUCTION_BACKEND_URL
).replace(/\/+$/, "");

export const ACCEPTED_FILE_TYPES = [
  "image/png",
  "image/jpeg",
  "image/jpg",
  "image/webp",
] as const;

export const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"] as const;

export const MAX_FILE_SIZE_MB = 25;

export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
