"""Hybrid document analysis pipeline.

Pipeline (no LLM required):
1. PDF text extraction — pdfplumber (falls back gracefully if not installed)
2. Date detection      — regex patterns for French/ISO date formats
3. Doc-type detection  — keyword scoring per document type
4. Patient matching    — rapidfuzz token sort ratio (falls back to difflib)
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field


# ── French month mapping ──────────────────────────────────────────────────────

_FR_MONTHS = {
    "janvier": "01", "février": "02", "fevrier": "02",
    "mars": "03", "avril": "04", "mai": "05", "juin": "06",
    "juillet": "07", "août": "08", "aout": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12", "decembre": "12",
}
_EN_MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

# ── Keyword map (doc_type → list of lower-case keywords) ─────────────────────

_TYPE_KEYWORDS: dict[str, list[str]] = {
    "prescription": [
        "ordonnance", "prescription", "médicament", "medicament",
        "posologie", "comprimé", "comprimes", "gélule", "gelule",
        "mg", "ml ", "cp ", "gel ", "sirop", "injectable",
    ],
    "medical_certificate": [
        "certificat", "certificate", "aptitude", "inapte", "apte au travail",
        "arrêt de travail", "arret de travail", "work stoppage",
        "visite médicale", "visite medicale", "médecin du travail", "medecin du travail",
    ],
    "medical_report": [
        "compte rendu", "compte-rendu", "rapport médical", "bilan médical",
        "consultation médicale", "diagnostic", "synthèse médicale",
    ],
    "medical_analysis": [
        "analyse", "biologie", "hémoglobine", "hemoglobine",
        "leucocyte", "plaquette", "sérologie", "serologie",
        "résultat", "resultat", "laboratoire", "glycémie", "glycemie",
        "cholestérol", "cholesterol", "créatinine", "creatinine",
    ],
    "letter": [
        "courrier", "lettre", "cher confrère", "confrere",
        "monsieur le docteur", "madame le docteur",
        "à l'attention", "a l'attention",
    ],
    "xray": [
        "radiographie", "radio", "cliché", "cliche", "incidence",
        "rx ", " rx\n",
    ],
    "ct_scan": [
        "scanner", "tomodensitométrie", "tomodensitometrie", "tdm",
        "coupe axiale",
    ],
    "mri": [
        "irm", "imagerie par résonance", "imagerie par resonance", "mri",
        "resonance magnétique", "resonance magnetique",
    ],
    "ultrasound": [
        "échographie", "echographie", "doppler", "sonographie",
    ],
}


@dataclass
class AnalysisResult:
    doc_type: str = ""
    doc_date: str = ""           # YYYY-MM-DD or ""
    patient_name: str = ""       # raw text found near patient keywords
    description: str = ""        # first non-empty meaningful line
    hints: list[str] = field(default_factory=list)


class DocumentAnalysisService:
    """Stateless analysis service — all methods are class methods."""

    # ── Text extraction ───────────────────────────────────────────────────────

    @classmethod
    def extract_text(cls, file_bytes: bytes, mime_type: str | None) -> str:
        mime = (mime_type or "").lower()
        if "pdf" in mime:
            return cls._extract_pdf_text(file_bytes)
        # Images: no OCR without tesseract — return empty
        return ""

    @classmethod
    def _extract_pdf_text(cls, file_bytes: bytes) -> str:
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages[:6]:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                return "\n".join(pages_text)
        except Exception:
            return ""

    # ── Date detection ────────────────────────────────────────────────────────

    @classmethod
    def detect_dates(cls, text: str) -> list[str]:
        """Return all dates found as YYYY-MM-DD strings, sorted descending."""
        found: set[str] = set()
        t = text

        # dd/mm/yyyy  or  dd-mm-yyyy  or  dd.mm.yyyy
        for m in re.finditer(r'\b(\d{1,2})[/\-\.](\d{2})[/\-\.](\d{4})\b', t):
            d, mo, y = m.group(1).zfill(2), m.group(2), m.group(3)
            if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                found.add(f"{y}-{mo}-{d}")

        # yyyy-mm-dd
        for m in re.finditer(r'\b(\d{4})-(\d{2})-(\d{2})\b', t):
            y, mo, d = m.group(1), m.group(2), m.group(3)
            if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                found.add(f"{y}-{mo}-{d}")

        # "12 janvier 2025" / "12 january 2025"
        all_months = {**_FR_MONTHS, **_EN_MONTHS}
        month_pattern = "|".join(all_months.keys())
        for m in re.finditer(
            rf'\b(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})\b', t, re.IGNORECASE
        ):
            d = m.group(1).zfill(2)
            mo = all_months[m.group(2).lower()]
            y = m.group(3)
            if 1 <= int(d) <= 31:
                found.add(f"{y}-{mo}-{d}")

        return sorted(found, reverse=True)

    # ── Document type detection ───────────────────────────────────────────────

    @classmethod
    def detect_doc_type(cls, text: str) -> tuple[str, str]:
        """Return (doc_type, hint_message). Empty strings if nothing detected."""
        tl = text.lower()
        scores: dict[str, int] = {}
        for dtype, keywords in _TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in tl)
            if score:
                scores[dtype] = score
        if not scores:
            return "", ""
        best = max(scores, key=lambda k: scores[k])
        label = best.replace("_", " ").title()
        return best, f"Detected from keywords: {label}"

    # ── Patient name extraction ───────────────────────────────────────────────

    @classmethod
    def detect_patient_name(cls, text: str) -> str:
        """Try to find a patient name near common French medical keywords."""
        # Look for patterns like "Nom : Dupont" / "Patient : Marie Dupont"
        patterns = [
            r'(?:patient|nom\s*[:/]\s*|nom\s+du\s+patient\s*[:/]?)\s*:?\s*([A-ZÀ-Ÿa-zà-ÿ\-\' ]{3,50})',
            r'(?:prénom\s*[:/]?\s*)([A-ZÀ-Ÿa-zà-ÿ\-\' ]{2,30})\s+(?:nom\s*[:/]?\s*)([A-ZÀ-Ÿa-zà-ÿ\-\' ]{2,30})',
            r'(?:m\.|mme\.?|mr\.?|dr\.?)\s+([A-ZÀ-Ÿa-zà-ÿ\-\' ]{3,50})',
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                name = " ".join(g for g in m.groups() if g).strip()
                if len(name) >= 3:
                    return name
        return ""

    # ── Patient fuzzy matching ────────────────────────────────────────────────

    @classmethod
    def match_patient(
        cls, detected_name: str, patients: list
    ) -> tuple[str, str]:
        """Fuzzy-match *detected_name* against *patients* list.

        Returns (patient_id, patient_label) or ("", "") if no good match.
        """
        if not detected_name or not patients:
            return "", ""

        name_map: dict[str, str] = {str(p.id): p.get_full_name() for p in patients}

        try:
            from rapidfuzz import fuzz, process as rf_process
            result = rf_process.extractOne(
                detected_name,
                list(name_map.values()),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=60,
            )
            if result:
                matched_name = result[0]
                pid = next(k for k, v in name_map.items() if v == matched_name)
                return pid, matched_name
        except ImportError:
            import difflib
            lower_map = {k: v.lower() for k, v in name_map.items()}
            matches = difflib.get_close_matches(
                detected_name.lower(),
                list(lower_map.values()),
                n=1,
                cutoff=0.6,
            )
            if matches:
                pid = next(k for k, v in lower_map.items() if v == matches[0])
                return pid, name_map[pid]

        return "", ""

    # ── Full pipeline ─────────────────────────────────────────────────────────

    @classmethod
    def analyze(
        cls,
        file_bytes: bytes,
        mime_type: str | None,
        patients: list,
    ) -> AnalysisResult:
        """Extract text from bytes then run the analysis pipeline."""
        text = cls.extract_text(file_bytes, mime_type)
        result = cls.analyze_text(text, patients)
        if not text:
            result.hints = [
                "No text could be extracted (image or encrypted PDF — please fill manually)."
            ]
        return result

    @classmethod
    def analyze_text(cls, text: str, patients: list) -> AnalysisResult:
        """Run the analysis pipeline on already-extracted text.

        Used by the Reflex annotation page which receives DocumentText resources
        (text already extracted by DocumentTextExtractionTask).
        """
        result = AnalysisResult()
        hints: list[str] = []

        if not text:
            result.hints = hints
            return result

        # Date
        dates = cls.detect_dates(text)
        if dates:
            result.doc_date = dates[0]
            hints.append(f"Date detected: {dates[0]}")

        # Doc type
        doc_type, type_hint = cls.detect_doc_type(text)
        if doc_type:
            result.doc_type = doc_type
            hints.append(type_hint)

        # Patient name
        raw_name = cls.detect_patient_name(text)
        if raw_name:
            result.patient_name = raw_name
            pid, label = cls.match_patient(raw_name, patients)
            if pid:
                hints.append(f"Patient matched: {label}")
            else:
                hints.append(f"Patient name found: '{raw_name}' — no close match in database")

        # Description: first non-trivial line
        for line in text.splitlines():
            line = line.strip()
            if len(line) > 15:
                result.description = line[:120]
                break

        result.hints = hints
        return result
