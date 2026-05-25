import axios, { AxiosError } from "axios";

import { API_BASE_URL } from "@/lib/constants";
import type { ExtractionResponse } from "@/types/extraction";

/** First /extract on Render may load OCR; allow up to 5 minutes. */
const EXTRACT_TIMEOUT_MS = 300_000;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: EXTRACT_TIMEOUT_MS,
});

export async function extractDocument(
  file: File,
  extractionPrompt: string,
): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("extraction_prompt", extractionPrompt);

  // Do not set Content-Type manually — Axios must add the multipart boundary.
  const { data } = await api.post<ExtractionResponse>("/extract", formData);

  return data;
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
        "Request timed out. The server may still be loading OCR models on first run — " +
        "wait a minute and try again, or check Render logs."
      );
    }
    if (axiosError.message) return axiosError.message;
  }

  if (error instanceof Error) return error.message;
  return "An unexpected error occurred. Please try again.";
}
