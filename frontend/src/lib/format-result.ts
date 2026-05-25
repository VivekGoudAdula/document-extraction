import type { JsonValue } from "@/types/extraction";

const ANSWER_KEYS = ["answer", "response", "result", "summary", "content", "explanation"];
const SKIP_KEYS = new Set(["question", "note", "source"]);

export type DisplayContent =
  | { mode: "empty" }
  | { mode: "answer"; question?: string; answer: string }
  | { mode: "fields"; question?: string; items: { label: string; value: unknown }[] };

function humanizeLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function getPrimaryAnswer(data: JsonValue): string | null {
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;

  const record = data as Record<string, unknown>;

  for (const key of ANSWER_KEYS) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return null;
}

export function getDisplayContent(data: JsonValue): DisplayContent {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return { mode: "empty" };
  }

  const record = data as Record<string, unknown>;
  const question =
    typeof record.question === "string" && record.question.trim()
      ? record.question.trim()
      : undefined;

  const answer = getPrimaryAnswer(data);
  const otherItems = Object.entries(record)
    .filter(
      ([key]) =>
        !SKIP_KEYS.has(key) && !ANSWER_KEYS.includes(key) && key !== "question",
    )
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([key, value]) => ({ label: humanizeLabel(key), value }));

  if (answer && otherItems.length === 0) {
    return { mode: "answer", question, answer };
  }

  const items: { label: string; value: unknown }[] = [];
  if (answer) {
    items.push({ label: "Answer", value: answer });
  }
  items.push(...otherItems);

  if (items.length === 0) {
    return { mode: "empty" };
  }

  return { mode: "fields", question, items };
}

export function formatValueAsPlainText(value: unknown, indent = 0): string {
  const pad = "  ".repeat(indent);

  if (value === null || value === undefined) return `${pad}—`;
  if (typeof value === "string") return `${pad}${value.trim()}`;
  if (typeof value === "number" || typeof value === "boolean") {
    return `${pad}${String(value)}`;
  }

  if (Array.isArray(value)) {
    return value
      .map((item, index) => {
        if (typeof item === "string" || typeof item === "number") {
          return `${pad}• ${String(item)}`;
        }
        return `${pad}${index + 1}.\n${formatValueAsPlainText(item, indent + 1)}`;
      })
      .join("\n");
  }

  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(
        ([key, child]) =>
          `${pad}${humanizeLabel(key)}:\n${formatValueAsPlainText(child, indent + 1)}`,
      )
      .join("\n\n");
  }

  return `${pad}${String(value)}`;
}

export function formatDisplayAsPlainText(content: DisplayContent): string {
  if (content.mode === "empty") return "";
  if (content.mode === "answer") {
    const parts = [];
    if (content.question) parts.push(`Question: ${content.question}`, "");
    parts.push(content.answer);
    return parts.join("\n").trim();
  }

  const parts: string[] = [];
  if (content.question) {
    parts.push(`Question: ${content.question}`, "");
  }
  for (const item of content.items) {
    parts.push(`${item.label}\n${formatValueAsPlainText(item.value, 1)}`, "");
  }
  return parts.join("\n").trim();
}

/** @deprecated Use getDisplayContent — kept for compatibility */
export function getFieldEntries(
  data: JsonValue,
): { label: string; value: string }[] {
  const content = getDisplayContent(data);
  if (content.mode !== "fields") return [];
  return content.items.map((item) => ({
    label: item.label,
    value: formatValueAsPlainText(item.value, 0),
  }));
}
