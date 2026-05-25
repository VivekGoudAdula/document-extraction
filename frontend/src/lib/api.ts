import axios, { AxiosError } from "axios";

import { API_BASE_URL } from "@/lib/constants";
import type { ExtractionResponse } from "@/types/extraction";

/** First /extract on Render may load OCR models; allow up to 10 minutes. */
const EXTRACT_TIMEOUT_MS = 600_000;
const HEALTH_TIMEOUT_MS = 60_000;

const RETRYABLE_STATUSES = new Set([502, 503, 504]);
const MAX_EXTRACT_ATTEMPTS = 4;
const RETRY_DELAY_MS = 20_000;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: EXTRACT_TIMEOUT_MS,
});

const healthApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: HEALTH_TIMEOUT_MS,
});

export type HealthStatus = {
  status?: string;
  mongodb?: string;
  paddle_models_cached?: boolean;
  paddleocr_loaded?: boolean;
};

export async function fetchHealth(): Promise<HealthStatus> {
  const { data } = await healthApi.get<HealthStatus>("/health");
  return data;
}

/** Wake Render free tier before the user uploads (cold start ~30–60s). */
export async function wakeBackend(): Promise<HealthStatus | null> {
  try {
    return await fetchHealth();
  } catch {
    return null;
  }
}

function isRetryableExtractError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status !== undefined && RETRYABLE_STATUSES.has(status)) return true;
  if (!error.response && error.code !== "ECONNABORTED") return true;
  return false;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function extractDocument(
  file: File,
  extractionPrompt: string,
): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("extraction_prompt", extractionPrompt);

  let lastError: unknown;

  for (let attempt = 1; attempt <= MAX_EXTRACT_ATTEMPTS; attempt++) {
    try {
      const { data } = await api.post<ExtractionResponse>("/extract", formData);
      return data;
    } catch (error) {
      lastError = error;
      if (attempt < MAX_EXTRACT_ATTEMPTS && isRetryableExtractError(error)) {
        await delay(RETRY_DELAY_MS);
        await wakeBackend();
        continue;
      }
      throw error;
    }
  }

  throw lastError;
}

type ApiErrorBody = {
  detail?: string | { msg: string; loc?: (string | number)[] }[];
  errors?: { msg: string; loc?: (string | number)[] }[];
  error?: string;
};

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>;
    const data = axiosError.response?.data;

    if (typeof data?.detail === "string") return data.detail;

    if (Array.isArray(data?.detail)) {
      return data.detail.map((e) => e.msg).join("; ");
    }

    if (Array.isArray(data?.errors) && data.errors.length > 0) {
      return data.errors.map((e) => e.msg).join("; ");
    }

    if (typeof data?.error === "string") return data.error;
    if (axiosError.code === "ECONNABORTED") {
      return (
        "Request timed out. OCR on the free cloud tier can take several minutes — " +
        "wait and try once more (only one upload at a time)."
      );
    }
    if (axiosError.response?.status === 502) {
      return (
        "Backend restarted or ran out of memory (502). Wait ~30 seconds and try again. " +
        "Avoid uploading several images at once on the free Render plan."
      );
    }
    if (!axiosError.response) {
      return (
        "Cannot reach the API. If the browser shows CORS, the backend likely returned 502 " +
        "after a crash — wait for Render to finish starting, then retry."
      );
    }
    if (axiosError.message) return axiosError.message;
  }

  if (error instanceof Error) return error.message;
  return "An unexpected error occurred. Please try again.";
}
