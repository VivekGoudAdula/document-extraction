"""
Fuse local PaddleOCR and TrOCR outputs for GPT semantic extraction.

Prefer TrOCR for handwriting; prefer PaddleOCR for layout-heavy printed text.
"""

import re

from app.models.ocr_models import OCRResult


class FusionService:
    def _normalize_lines(self, text: str) -> list[str]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        deduped: list[str] = []
        seen: set[str] = set()
        for line in lines:
            key = re.sub(r"\s+", " ", line.lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(line)
        return deduped

    def _format_paddle_section(self, result: OCRResult) -> str:
        if not result.get("success"):
            return f"PaddleOCR unavailable: {result.get('error', 'unknown error')}"

        text = (result.get("text") or "").strip()
        if not text:
            return "No PaddleOCR text available."

        lines = self._normalize_lines(text)
        confidences = result.get("confidence") or []
        avg_conf = None
        if confidences:
            scores = [
                float(entry["confidence"])
                for entry in confidences
                if entry.get("confidence") is not None
            ]
            if scores:
                avg_conf = sum(scores) / len(scores)

        body = "\n".join(lines)
        if avg_conf is not None:
            return f"{body}\n\n(Average PaddleOCR confidence: {avg_conf:.2f})"
        return body

    def _format_trocr_section(self, result: OCRResult) -> str:
        if not result.get("success"):
            return f"TrOCR unavailable: {result.get('error', 'unknown error')}"

        text = (result.get("text") or "").strip()
        if not text:
            return "No TrOCR text available."

        return "\n".join(self._normalize_lines(text))

    def build_combined_context(
        self,
        paddle_result: OCRResult,
        trocr_result: OCRResult,
    ) -> str:
        sections = [
            "PADDLE OCR:",
            self._format_paddle_section(paddle_result),
            "",
            "TrOCR:",
            self._format_trocr_section(trocr_result),
        ]

        trocr_text = (trocr_result.get("text") or "").strip()
        paddle_text = (paddle_result.get("text") or "").strip()
        if trocr_text and trocr_text != paddle_text:
            sections.extend(
                [
                    "",
                    "HANDWRITING HINT:",
                    "Prefer TrOCR lines for handwritten or difficult regions; "
                    "prefer PaddleOCR for printed layout, tables, and forms.",
                ]
            )

        return "\n".join(sections).strip()


fusion_service = FusionService()
