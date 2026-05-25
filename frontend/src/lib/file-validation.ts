import {
  ACCEPTED_EXTENSIONS,
  ACCEPTED_FILE_TYPES,
  MAX_FILE_SIZE_BYTES,
  MAX_FILE_SIZE_MB,
} from "@/lib/constants";

export function isAcceptedFile(file: File): boolean {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  const typeMatch = ACCEPTED_FILE_TYPES.includes(
    file.type as (typeof ACCEPTED_FILE_TYPES)[number],
  );
  const extensionMatch = ACCEPTED_EXTENSIONS.includes(
    extension as (typeof ACCEPTED_EXTENSIONS)[number],
  );
  return typeMatch || extensionMatch;
}

export function validateFile(file: File): string | null {
  if (!isAcceptedFile(file)) {
    return "Only PNG, JPG, JPEG, and WEBP images are supported.";
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return `File size must be under ${MAX_FILE_SIZE_MB} MB.`;
  }
  return null;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
