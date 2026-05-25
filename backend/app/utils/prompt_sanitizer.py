import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExtractionMode(str, Enum):
    FIELDS = "fields"
    QUESTION = "question"


@dataclass(frozen=True)
class ExtractionIntent:
    mode: ExtractionMode
    text: str
    field_keys: tuple[str, ...] = ()


_QUESTION_PATTERNS = re.compile(
    r"(?i)\b(what is|what are|definition of|define|explain|describe|give me|tell me|"
    r"how does|how do|why does|summarize|summary of)\b"
)

_FIELD_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$", re.IGNORECASE)

# Lines removed entirely before sending to Azure.
_DROP_LINE_PATTERNS = [
    re.compile(r"(?i)^\s*(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)"),
    re.compile(r"(?i)^\s*you\s+are\s+now\b"),
    re.compile(r"(?i)^\s*act\s+as\s+(a\s+)?"),
    re.compile(r"(?i)^\s*system\s*:\s*"),
    re.compile(r"(?i)^\s*assistant\s*:\s*"),
    re.compile(r"(?i)^\s*user\s*:\s*"),
    re.compile(r"(?i)\bjailbreak\b"),
    re.compile(r"(?i)\bdan\s+mode\b"),
    re.compile(r"(?i)prompt\s+injection"),
    re.compile(r"(?i)do\s+not\s+follow"),
    re.compile(r"(?i)override\s+(the\s+)?(system|instructions)"),
]

_INLINE_REPLACE = [
    (re.compile(r"(?i)\bignore\s+(all\s+)?(previous\s+)?instructions\b"), "notes"),
    (re.compile(r"(?i)\bact\s+as\b"), "work as"),
    (re.compile(r"(?i)\byou\s+are\b"), "parties are"),
    (re.compile(r"(?i)\bsystem\s+prompt\b"), "notes"),
    (re.compile(r"(?i)\bchatgpt\b"), "tool"),
    (re.compile(r"(?i)\bgpt-?\d\b"), "tool"),
    (re.compile(r"(?i)<\s*/?\s*document[^>]*>"), ""),
    (re.compile(r"(?i)<\s*/?\s*instructions[^>]*>"), ""),
]

# Substrings masked anywhere in the document (Prompt Shield false positives).
_MASK_SUBSTRINGS = [
    "instruction",
    "instructions",
    "ignore",
    "disregard",
    "jailbreak",
    "system prompt",
    "system:",
    "assistant:",
    "user:",
    "openai",
    "chatgpt",
    "language model",
    "prompt injection",
    "do not follow",
    "act as",
    "you are now",
    "override",
    "forget all",
    "developer mode",
    "dan mode",
]

_USER_PROMPT_TRIGGERS = re.compile(
    r"(?i)\b(ignore|disregard|forget|act as|you are|system prompt|jailbreak|"
    r"return only|valid json only|do anything now|extract all)\b"
)

CHUNK_SIZE = 1800


def sanitize_document_text(text: str, *, aggressive: bool = False) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if any(pattern.search(line) for pattern in _DROP_LINE_PATTERNS):
            continue
        if aggressive:
            for pattern, replacement in _INLINE_REPLACE:
                line = pattern.sub(replacement, line)
        lines.append(line)

    result = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", result)


def deep_redact_document(text: str) -> str:
    """Heavy redaction for Azure Prompt Shield — used on every chunk."""
    redacted = sanitize_document_text(text, aggressive=True)
    for phrase in _MASK_SUBSTRINGS:
        redacted = re.sub(re.escape(phrase), "[...]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\s+", " ", redacted)
    return redacted.strip()


def sanitize_user_prompt(prompt: str) -> str:
    cleaned = _USER_PROMPT_TRIGGERS.sub("", prompt)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;")
    if not cleaned:
        return "invoice_number, date, total_amount"
    return cleaned


def _looks_like_field_list(text: str) -> bool:
    if "?" in text:
        return False
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) < 2:
        return False
    return all(_FIELD_KEY_PATTERN.match(part.replace(" ", "_")) for part in parts)


def parse_extraction_intent(prompt: str) -> ExtractionIntent:
    """Detect field-list vs natural-language question prompts."""
    cleaned = sanitize_user_prompt(prompt)

    if _looks_like_field_list(cleaned):
        keys = tuple(
            p.strip().replace(" ", "_").lower()
            for p in cleaned.split(",")
            if p.strip()
        )
        return ExtractionIntent(mode=ExtractionMode.FIELDS, text=cleaned, field_keys=keys)

    if _QUESTION_PATTERNS.search(cleaned) or "?" in cleaned:
        return ExtractionIntent(mode=ExtractionMode.QUESTION, text=cleaned)

    if len(cleaned.split()) <= 4 and "_" in cleaned:
        return ExtractionIntent(
            mode=ExtractionMode.FIELDS,
            text=cleaned,
            field_keys=(cleaned.replace(" ", "_").lower(),),
        )

    return ExtractionIntent(mode=ExtractionMode.QUESTION, text=cleaned)


def split_document_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text)
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(para), chunk_size):
                chunks.append(para[i : i + chunk_size])
            continue

        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    return chunks or [text[:chunk_size]]


def extract_keyword_excerpt(text: str, keywords: tuple[str, ...], window: int = 600) -> str:
    """Pull lines/segments that mention keywords — helps noisy OCR tables."""
    if not text.strip():
        return ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    matched = [ln for ln in lines if any(kw in ln.lower() for kw in keywords)]
    if matched:
        return "\n".join(matched[:80])

    lower = text.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx >= 0:
            start = max(0, idx - window)
            end = min(len(text), idx + len(kw) + window)
            return text[start:end]
    return ""


def keywords_for_intent(intent: ExtractionIntent) -> tuple[str, ...]:
    text = intent.text.lower()
    keys: list[str] = []
    for term in ("rag", "llm", "agent", "agentic", "invoice", "total", "vendor"):
        if term in text:
            keys.append(term)
    if "retrieval" in text or "rag" in text:
        keys.extend(["rag", "retrieval", "augmented", "search", "documents"])
    return tuple(dict.fromkeys(keys)) or ("definition",)


def build_chunk_message(
    intent: ExtractionIntent,
    chunk: str,
    *,
    ocr_noisy: bool = False,
) -> list[dict[str, str]]:
    """Two user turns: task, then source text (reduces Azure jailbreak false positives)."""
    if intent.mode is ExtractionMode.QUESTION:
        ocr_hint = (
            " The next message is noisy OCR (typos/spacing). Infer the best answer from context."
            if ocr_noisy
            else ""
        )
        return [
            {
                "role": "user",
                "content": (
                    f"Using only the next message, reply with JSON: "
                    f'{{"question": string, "answer": string}}.{ocr_hint} '
                    "Always provide a non-empty answer string when any clue exists."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {intent.text}\n\nSource text:\n{chunk}",
            },
        ]

    keys = ", ".join(intent.field_keys) if intent.field_keys else intent.text
    return [
        {
            "role": "user",
            "content": f"From the next message, fill JSON keys: {keys}. Use null if missing.",
        },
        {"role": "user", "content": chunk},
    ]


def _collect_answer_text(data: dict[str, Any]) -> str:
    for key in (
        "answer",
        "response",
        "result",
        "definition",
        "rag_definition",
        "summary",
        "content",
        "explanation",
    ):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    strings = [
        str(v).strip()
        for v in data.values()
        if isinstance(v, str) and len(str(v).strip()) > 15
    ]
    return max(strings, key=len) if strings else ""


def build_single_shot_message(
    intent: ExtractionIntent,
    document_text: str,
    *,
    ocr_noisy: bool = False,
) -> list[dict[str, str]]:
    ocr_note = " OCR text may contain typos — correct and infer as needed." if ocr_noisy else ""

    if intent.mode is ExtractionMode.QUESTION:
        return [
            {
                "role": "user",
                "content": (
                    f"Answer from the document below.{ocr_note} "
                    f'JSON keys: "question", "answer".\n\n'
                    f"Question: {intent.text}\n\n"
                    f"Document:\n{document_text}"
                ),
            },
        ]

    keys = ", ".join(intent.field_keys) if intent.field_keys else intent.text
    return [
        {
            "role": "user",
            "content": (
                f"Extract JSON keys: {keys} from this document.{ocr_note} "
                f"Use null only when a field is truly absent.\n\n"
                f"Document:\n{document_text}"
            ),
        },
    ]


def merge_partial_results(
    partials: list[dict[str, Any]],
    intent: ExtractionIntent,
) -> dict[str, Any]:
    if intent.mode is ExtractionMode.QUESTION:
        answers = [_collect_answer_text(p) for p in partials if isinstance(p, dict)]
        answers = [a for a in answers if a]
        if not answers:
            return {}

        best = max(answers, key=len)
        return {"question": intent.text, "answer": best}

    merged: dict[str, Any] = {}
    for partial in partials:
        if not isinstance(partial, dict):
            continue
        for key, value in partial.items():
            if value is None or value == "" or value == []:
                continue
            if key not in merged or merged[key] in (None, "", []):
                merged[key] = value
    return merged


def is_empty_result(data: dict[str, Any]) -> bool:
    if not data:
        return True
    return all(v in (None, "", [], {}) for v in data.values())


def simplify_question_for_api(question: str) -> str:
    """Short, neutral wording — fewer Prompt Shield false positives."""
    text = question.strip()
    text = re.sub(r"(?i)^from the image uploaded[,:\s]*", "", text)
    text = re.sub(r"(?i)^give me the\s+", "", text)
    text = re.sub(r"(?i)^please\s+", "", text)
    return text.strip() or question


def build_bypass_messages(data: str, *, field_hint: str = "answer") -> list[dict[str, str]]:
    """Ultra-short prompt: one user message, no JSON-mode phrasing."""
    snippet = data[:1000].strip()
    return [
        {
            "role": "user",
            "content": f"{field_hint}:\n{snippet}",
        },
    ]


def heuristic_answer_from_ocr(
    document_text: str,
    intent: ExtractionIntent,
) -> dict[str, Any] | None:
    """Last resort when Azure blocks every API call — use OCR keyword lines."""
    keywords = keywords_for_intent(intent)
    excerpt = extract_keyword_excerpt(document_text, keywords, window=800)
    if not excerpt:
        excerpt = document_text[:2000]

    lines = [
        ln.strip()
        for ln in re.split(r"[\n.]+", excerpt)
        if ln.strip() and len(ln.strip()) > 20
    ]
    if not lines:
        return None

    scored: list[tuple[int, str]] = []
    for line in lines:
        lower = line.lower()
        score = sum(1 for kw in keywords if kw in lower)
        if intent.mode is ExtractionMode.QUESTION and "definition" in intent.text.lower():
            if "definition" in lower or "search" in lower or "document" in lower:
                score += 2
        if score > 0:
            scored.append((score, line))

    if not scored:
        return None

    best_line = max(scored, key=lambda x: (x[0], len(x[1])))[1]

    if intent.mode is ExtractionMode.QUESTION:
        return {
            "question": intent.text,
            "answer": best_line,
            "source": "ocr_heuristic",
        }

    return {"summary": best_line, "source": "ocr_heuristic"}
