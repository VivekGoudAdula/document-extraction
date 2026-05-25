/** Set on Vercel: NEXT_PUBLIC_API_URL = your Render backend URL (no trailing slash) */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
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
