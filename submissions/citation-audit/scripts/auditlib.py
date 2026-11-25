#!/usr/bin/env python3
"""Deterministic span matching for citation-audit. Standard library only."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

VERIFIER_VERSION = "1.0.0"
SUPPORTED_MIN = 0.95
PARTIAL_MIN = 0.75
MAX_BYTES = 20 * 1024 * 1024
CLAIM_TYPES = ("quantitative", "quotation", "attribution", "paraphrase", "causal")
VERDICT_ORDER = {"STALE": 0, "UNSUPPORTED": 1, "PARTIAL": 2, "SUPPORTED": 3}

CURRENCY = {"usd", "eur", "gbp", "jpy"}
SCALE = {"thousand", "million", "billion"}
MEASURE = {
    "percent",
    "hour",
    "hours",
    "day",
    "days",
    "week",
    "weeks",
    "month",
    "months",
    "year",
    "years",
    "minute",
    "minutes",
    "second",
    "seconds",
    "kg",
    "kilogram",
    "kilograms",
    "ton",
    "tons",
    "tonne",
    "tonnes",
    "mile",
    "miles",
    "km",
    "kilometer",
    "kilometers",
}
NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
    "thirty": "30",
    "forty": "40",
    "fifty": "50",
    "sixty": "60",
    "seventy": "70",
    "eighty": "80",
    "ninety": "90",
}
CONTRACTIONS = {
    "don't": "do not",
    "dont": "do not",
    "doesn't": "does not",
    "doesnt": "does not",
    "didn't": "did not",
    "didnt": "did not",
    "isn't": "is not",
    "isnt": "is not",
    "aren't": "are not",
    "arent": "are not",
    "wasn't": "was not",
    "wasnt": "was not",
    "weren't": "were not",
    "werent": "were not",
    "haven't": "have not",
    "havent": "have not",
    "hasn't": "has not",
    "hasnt": "has not",
    "hadn't": "had not",
    "hadnt": "had not",
    "won't": "will not",
    "wont": "will not",
    "wouldn't": "would not",
    "wouldnt": "would not",
    "shouldn't": "should not",
    "shouldnt": "should not",
    "couldn't": "could not",
    "couldnt": "could not",
    "can't": "cannot",
    "cant": "cannot",
    "cannot": "cannot",
}
NEGATION = {"not", "never", "without", "cannot", "no"}
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CAUSAL_RE = re.compile(
    r"\b(because|therefore|caused|causes|cause|leads to|led to|driven by|results in|resulted in)\b",
    re.I,
)
ATTRIB_RE = re.compile(r"\b(according to|said|stated|reported|wrote|told)\b", re.I)


class AuditError(Exception):
    """Input the script cannot certify. Exit code 2."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def read_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise AuditError(f"File not found: {path}")
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise AuditError(f"{path.name} exceeds the 20 MB limit ({size} bytes).")
    return path.read_bytes()


def decode_text(data: bytes, label: str) -> str:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise AuditError(f"{label} is not UTF-8. Save the file as UTF-8 and run again.")


def normalize(text: str) -> str:
    text = unicodedata_nfkc(text)
    text = text.replace("%", " percent ")
    text = text.replace("$", " usd ")
    text = text.replace("€", " eur ")
    text = text.replace("£", " gbp ")
    text = text.replace("¥", " jpy ")
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = text.casefold()
    for src, dst in CONTRACTIONS.items():
        text = re.sub(rf"\b{re.escape(src)}\b", dst, text)
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    # Keep a decimal point between digits. Every other period is sentence punctuation.
    text = re.sub(r"(?<!\d)\.(?!\d)", " ", text)
    text = re.sub(r"\.(?!\d)", " ", text)
    text = re.sub(r"[^\w\s.+-]", " ", text, flags=re.UNICODE)
    tokens = []
    for tok in text.split():
        tokens.append(NUMBER_WORDS.get(tok, tok))
    return " ".join(tokens)


def unicodedata_nfkc(text: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFKC", text)


def tokens_of(norm: str) -> list[str]:
    return norm.split()


def is_number(token: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", token))


def canon_number(token: str) -> str:
    if "." in token:
        token = token.rstrip("0").rstrip(".")
    return token or "0"


def extract_numbers(norm: str) -> tuple[tuple[str, str], ...]:
    toks = tokens_of(norm)
    found: list[tuple[str, str]] = []
    i = 0
    while i < len(toks):
        tok = toks[i]
        if tok in CURRENCY and i + 1 < len(toks) and is_number(toks[i + 1]):
            num = canon_number(toks[i + 1])
            unit = tok
            i += 2
            if i < len(toks) and toks[i] in SCALE:
                unit = f"{unit} {toks[i]}"
                i += 1
            found.append((num, unit))
            continue
        if is_number(tok):
            num = canon_number(tok)
            unit = ""
            i += 1
            if i < len(toks) and toks[i] in SCALE:
                scale = toks[i]
                i += 1
                if i < len(toks) and toks[i] in CURRENCY:
                    unit = f"{toks[i]} {scale}"
                    i += 1
                else:
                    unit = scale
            elif i < len(toks) and toks[i] in CURRENCY:
                unit = toks[i]
                i += 1
            elif i < len(toks) and toks[i] in MEASURE:
                unit = toks[i]
                i += 1
            found.append((num, unit))
            continue
        i += 1
    return tuple(found)


def bind_tokens(norm: str) -> list[str]:
    """Move a currency token onto the number it binds so order does not change equality."""
    toks = tokens_of(norm)
    out: list[str] = []
    i = 0
    while i < len(toks):
        tok = toks[i]
        if tok in CURRENCY and i + 1 < len(toks) and is_number(toks[i + 1]):
            num = toks[i + 1]
            extra = ""
            i += 2
            if i < len(toks) and toks[i] in SCALE:
                extra = " " + toks[i]
                i += 1
            out.extend([num, f"{tok}{extra}".strip()])
            continue
        if is_number(tok):
            num = tok
            i += 1
            if i < len(toks) and toks[i] in SCALE:
                scale = toks[i]
                i += 1
                if i < len(toks) and toks[i] in CURRENCY:
                    out.extend([num, f"{toks[i]} {scale}"])
                    i += 1
                else:
                    out.extend([num, scale])
            elif i < len(toks) and toks[i] in CURRENCY:
                out.extend([num, toks[i]])
                i += 1
            else:
                out.append(num)
            continue
        out.append(tok)
        i += 1
    return [t for t in out if t]


def negation_set(norm: str) -> frozenset[str]:
    toks = tokens_of(norm)
    found: set[str] = set()
    for i, tok in enumerate(toks):
        if tok in {"not", "never", "without", "cannot"}:
            found.add(tok)
        elif tok == "no":
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if not is_number(nxt):
                found.add("no")
    return frozenset(found)


def numbers_cover(claim_nums: tuple[tuple[str, str], ...], span_nums: tuple[tuple[str, str], ...]) -> bool:
    span = Counter(span_nums)
    for item in claim_nums:
        if span[item] <= 0:
            return False
        span[item] -= 1
    return True


def skeleton(norm: str) -> str:
    parts: list[str] = []
    nums = extract_numbers(norm)
    # Replace number occurrences left to right using the extractor's walk.
    toks = tokens_of(norm)
    i = 0
    ni = 0
    while i < len(toks):
        start = i
        # Reuse extract walk by comparing prefixes is messy; mark tokens that are numeric pieces.
        tok = toks[i]
        if tok in CURRENCY and i + 1 < len(toks) and is_number(toks[i + 1]):
            parts.append("#")
            if ni < len(nums):
                parts.append(nums[ni][1])
                ni += 1
            i += 2
            if i < len(toks) and toks[i] in SCALE:
                i += 1
            continue
        if is_number(tok):
            parts.append("#")
            unit = nums[ni][1] if ni < len(nums) else ""
            if unit:
                parts.append(unit)
            if ni < len(nums):
                ni += 1
            i += 1
            if i < len(toks) and toks[i] in SCALE:
                i += 1
                if i < len(toks) and toks[i] in CURRENCY:
                    i += 1
            elif i < len(toks) and (toks[i] in CURRENCY or toks[i] in MEASURE):
                i += 1
            continue
        parts.append(tok)
        i += 1
        if i == start:
            break
    return " ".join(p for p in parts if p)


def sequence_ratio(a: str, b: str) -> float:
    import difflib

    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    # Exact matches are decided before this. Cap the fuzzy comparison so a
    # huge pasted file cannot spend quadratic time in the matcher.
    if len(a) > 4000 or len(b) > 4000:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_start(hay: list[str], needle: list[str]) -> int | None:
    if not needle or len(needle) > len(hay):
        return None
    width = len(needle)
    for i in range(len(hay) - width + 1):
        if hay[i : i + width] == needle:
            return i
    return None


def contiguous(hay: list[str], needle: list[str]) -> bool:
    return find_start(hay, needle) is not None


def negated(norm: str) -> bool:
    return bool(negation_set(norm))


def leading_negation(tokens: list[str], start: int) -> bool:
    prev = tokens[max(0, start - 2) : start]
    return bool(negation_set(" ".join(prev)))


def token_pattern(token: str) -> str:
    if token == "percent":
        return r"(?:%|percent)"
    if token in CURRENCY:
        raw = {"usd": r"\$", "eur": "€", "gbp": "£", "jpy": "¥"}[token]
        return rf"(?:{raw}|{token})"
    if token in NUMBER_WORDS.values() or is_number(token):
        return re.escape(token)
    return re.escape(token)


def slice_quote(raw: str, claim_norm: str) -> str | None:
    toks = tokens_of(claim_norm)
    if not toks:
        return None
    body = r"\W*".join(token_pattern(t) for t in toks)
    pattern = re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)
    match = pattern.search(raw)
    if not match:
        return None
    end = match.end()
    while end < len(raw) and raw[end] in "\"'”’».!?":
        end += 1
    return raw[match.start() : end].strip()


@dataclass
class Dated:
    iso: str
    precision: str  # day | year

    def strictly_newer_than(self, other: Dated) -> bool:
        if self.precision == "year" or other.precision == "year":
            return int(self.iso[:4]) > int(other.iso[:4])
        return self.iso > other.iso


def _valid_day(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def find_date(text: str, filename: str) -> Dated | None:
    # A date inside the body ("the March 2, 1999 storm") is not the file date.
    labeled = []
    for line in text.splitlines()[:120]:
        if re.search(r"\b(as of|updated|effective|revised|dated)\b", line, re.I):
            labeled.append(line)
    blob = "\n".join([Path(filename).stem, *labeled])
    found: list[Dated] = []
    for match in re.finditer(r"\b(19\d{2}|20\d{2})-(\d{2})-(\d{2})\b", blob):
        day = _valid_day(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if day:
            found.append(Dated(day.isoformat(), "day"))
    month_alt = "|".join(MONTHS)
    for match in re.finditer(rf"\b({month_alt})\s+(\d{{1,2}}),?\s+(19\d{{2}}|20\d{{2}})\b", blob, re.I):
        day = _valid_day(int(match.group(3)), MONTHS[match.group(1).casefold()], int(match.group(2)))
        if day:
            found.append(Dated(day.isoformat(), "day"))
    for match in re.finditer(rf"\b(\d{{1,2}})\s+({month_alt})\s+(19\d{{2}}|20\d{{2}})\b", blob, re.I):
        day = _valid_day(int(match.group(3)), MONTHS[match.group(2).casefold()], int(match.group(1)))
        if day:
            found.append(Dated(day.isoformat(), "day"))
    if found:
        return max(found, key=lambda item: item.iso)
    years = [int(y) for y in re.findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", Path(filename).stem)]
    if years:
        year = max(years)
        return Dated(f"{year}-01-01", "year")
    return None


def split_sentences(text: str) -> list[str]:
    chunks: list[str] = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        protected = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", line)
        for bit in re.split(r"(?<=[.!?])\s+", protected):
            bit = bit.replace("<DOT>", ".").strip()
            if bit:
                chunks.append(bit)
    return chunks


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</p>", "\n", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(raw)


def read_docx(data: bytes) -> list[tuple[str, str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            info = package.getinfo("word/document.xml")
            if info.file_size > MAX_BYTES:
                raise AuditError("DOCX document.xml exceeds the 20 MB uncompressed limit.")
            xml = package.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise AuditError(f"Could not read DOCX: {exc}") from exc
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise AuditError(f"Could not parse DOCX XML: {exc}") from exc
    blocks: list[tuple[str, str]] = []
    index = 0
    for para in root.iter(W_NS + "p"):
        parts: list[str] = []
        for node in para.iter():
            if node.tag == W_NS + "t" and node.text:
                parts.append(node.text)
            elif node.tag in {W_NS + "tab", W_NS + "br", W_NS + "cr"}:
                parts.append(" ")
        text = re.sub(r"\s+", " ", "".join(parts)).strip()
        if not text:
            continue
        index += 1
        blocks.append((f"paragraph {index}", text))
    if not blocks:
        raise AuditError("DOCX has no extractable paragraph text.")
    return blocks


def read_pdf(path: Path) -> list[tuple[str, str]]:
    errors: list[str] = []
    try:
        import pdfplumber  # type: ignore

        blocks: list[tuple[str, str]] = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                for j, sentence in enumerate(split_sentences(text), 1):
                    blocks.append((f"page {i} sentence {j}", sentence))
        if blocks:
            return blocks
        errors.append("pdfplumber extracted no text")
    except ImportError:
        errors.append("pdfplumber is not installed")
    except Exception as exc:  # library-specific failures stay non-fatal
        errors.append(f"pdfplumber failed ({exc})")
    try:
        import pypdfium2  # type: ignore

        blocks = []
        pdf = pypdfium2.PdfDocument(str(path))
        try:
            for i in range(len(pdf)):
                page = pdf[i]
                textpage = page.get_textpage()
                text = textpage.get_text_bounded() or ""
                for j, sentence in enumerate(split_sentences(text), 1):
                    blocks.append((f"page {i + 1} sentence {j}", sentence))
        finally:
            pdf.close()
        if blocks:
            return blocks
        errors.append("pypdfium2 extracted no text")
    except ImportError:
        errors.append("pypdfium2 is not installed")
    except Exception as exc:
        errors.append(f"pypdfium2 failed ({exc})")
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        blocks = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            for j, sentence in enumerate(split_sentences(text), 1):
                blocks.append((f"page {i} sentence {j}", sentence))
        if blocks:
            return blocks
        errors.append("pypdf extracted no text")
    except ImportError:
        errors.append("pypdf is not installed")
    except Exception as exc:
        errors.append(f"pypdf failed ({exc})")
    raise AuditError(
        "Cannot extract PDF text with an already-installed reader "
        "(pdfplumber, pypdfium2, or pypdf). "
        + "; ".join(errors)
        + ". This skill does not install packages."
    )


def load_document(path: Path) -> tuple[str, list[tuple[str, str]], bytes]:
    data = read_bytes(path)
    suffix = path.suffix.casefold()
    if suffix == ".docx":
        blocks = read_docx(data)
        text = "\n".join(piece for _, piece in blocks)
        return text, blocks, data
    if suffix == ".pdf":
        blocks = read_pdf(path)
        text = "\n".join(piece for _, piece in blocks)
        return text, blocks, data
    raw = decode_text(data, path.name)
    if suffix in {".html", ".htm"}:
        raw = html_to_text(raw)
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []
    for i, line in enumerate(lines, 1):
        if line.strip():
            blocks.append((f"line {i}", line.strip()))
    if not blocks:
        raise AuditError(f"{path.name} has no text.")
    return raw, blocks, data


def document_record(path: Path) -> dict:
    text, blocks, data = load_document(path)
    dated = find_date(text, path.name)
    return {
        "path": str(path),
        "name": path.name,
        "sha256": sha256_bytes(data),
        "date": dated.iso if dated else None,
        "date_precision": dated.precision if dated else None,
        "blocks": [{"anchor": anchor, "text": piece} for anchor, piece in blocks],
    }


def text_record(name: str, text: str) -> dict:
    data = text.encode("utf-8")
    if len(data) > MAX_BYTES:
        raise AuditError(f"{name} exceeds the 20 MB limit.")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = [(f"line {i}", line.strip()) for i, line in enumerate(lines, 1) if line.strip()]
    if not blocks:
        raise AuditError(f"{name} has no text.")
    dated = find_date(text, name)
    return {
        "path": name,
        "name": name,
        "sha256": sha256_bytes(data),
        "date": dated.iso if dated else None,
        "date_precision": dated.precision if dated else None,
        "blocks": [{"anchor": anchor, "text": piece} for anchor, piece in blocks],
    }


@dataclass
class Span:
    source_path: str
    source_name: str
    source_sha256: str
    source_date: str | None
    source_precision: str | None
    anchor: str
    raw: str
    norm: str
    score: float
    kind: str
    numbers: tuple[tuple[str, str], ...]
    negated: bool
    role: str  # support | contradiction


def iter_candidates(source: dict) -> list[tuple[str, str]]:
    base = [(block["anchor"], block["text"]) for block in source["blocks"]]
    sentences: list[tuple[str, str]] = []
    for anchor, text in base:
        parts = split_sentences(text)
        if len(parts) <= 1:
            sentences.append((anchor, text))
        else:
            for i, part in enumerate(parts, 1):
                sentences.append((f"{anchor} sentence {i}", part))
    paired: list[tuple[str, str]] = []
    for i in range(len(sentences) - 1):
        a, b = sentences[i], sentences[i + 1]
        paired.append((f"{a[0]} + {b[0]}", f"{a[1]} {b[1]}"))
    return sentences + paired


def score_span(claim_norm: str, span_norm: str) -> tuple[float, str]:
    if not claim_norm or not span_norm:
        return 0.0, "empty"
    claim_toks = tokens_of(claim_norm)
    span_toks = tokens_of(span_norm)
    if not claim_toks or not span_toks:
        return 0.0, "empty"
    start = find_start(span_toks, claim_toks)
    bound = contiguous(bind_tokens(span_norm), bind_tokens(claim_norm))
    if start is not None or bound:
        if not numbers_cover(extract_numbers(claim_norm), extract_numbers(span_norm)):
            return 0.0, "number"
        # "No, the plant exceeded" flips the positive words that follow.
        # "No, the plant did not exceed" keeps the negation already in the claim.
        if start is not None and leading_negation(span_toks, start) and not negated(claim_norm):
            return 0.0, "negation"
        return 1.0, "exact"
    if negated(claim_norm) != negated(span_norm):
        return 0.0, "negation"
    if not numbers_cover(extract_numbers(claim_norm), extract_numbers(span_norm)):
        return 0.0, "number"
    ratio = len(span_toks) / len(claim_toks)
    if ratio < 0.5 or ratio > 2.0:
        return 0.0, "length"
    seq = sequence_ratio(claim_norm, span_norm)
    sort_r = sequence_ratio(" ".join(sorted(claim_toks)), " ".join(sorted(span_toks)))
    sort_capped = min(sort_r, 0.94)
    if seq >= sort_capped:
        return round(seq, 4), "sequence"
    return round(sort_capped, 4), "token-sort"


def _without_negation(norm: str) -> str:
    return " ".join(tok for tok in tokens_of(norm) if tok not in NEGATION)


def contradiction_score(claim_norm: str, span_norm: str) -> float:
    """How close a span is when number or negation disagreement blocks support."""
    left = skeleton(_without_negation(claim_norm))
    right = skeleton(_without_negation(span_norm))
    claim_toks = tokens_of(left)
    span_toks = tokens_of(right)
    if not claim_toks or not span_toks:
        return 0.0
    if contiguous(bind_tokens(right), bind_tokens(left)):
        return 1.0
    ratio = len(span_toks) / len(claim_toks)
    if ratio < 0.5 or ratio > 2.0:
        return 0.0
    return round(sequence_ratio(left, right), 4)


def unit_values(nums: tuple[tuple[str, str], ...]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for value, unit in nums:
        grouped.setdefault(unit, []).append(value)
    return grouped


def numeric_conflict(a: tuple[tuple[str, str], ...], b: tuple[tuple[str, str], ...]) -> bool:
    """True when a shared unit has values and neither side contains the other."""
    left, right = unit_values(a), unit_values(b)
    for unit in set(left) & set(right):
        ca, cb = Counter(left[unit]), Counter(right[unit])
        if ca == cb:
            continue
        a_in_b = all(ca[key] <= cb[key] for key in ca)
        b_in_a = all(cb[key] <= ca[key] for key in cb)
        if a_in_b or b_in_a:
            continue
        return True
    return False


def make_span(source: dict, anchor: str, raw: str, claim_norm: str, score: float, kind: str, role: str) -> Span:
    norm = normalize(raw)
    return Span(
        source_path=source["path"],
        source_name=source["name"],
        source_sha256=source["sha256"],
        source_date=source.get("date"),
        source_precision=source.get("date_precision"),
        anchor=anchor,
        raw=raw,
        norm=norm,
        score=score,
        kind=kind,
        numbers=extract_numbers(norm),
        negated=negated(claim_norm) if role == "support" else negated(norm),
        role=role,
    )


def best_spans(claim_norm: str, sources: list[dict]) -> tuple[list[Span], list[Span]]:
    supports: list[Span] = []
    contradictions: list[Span] = []
    for source in sources:
        best_support: Span | None = None
        best_conflict: Span | None = None
        for anchor, raw in iter_candidates(source):
            span_norm = normalize(raw)
            score, kind = score_span(claim_norm, span_norm)
            if score > 0 and (best_support is None or score > best_support.score):
                best_support = make_span(source, anchor, raw, claim_norm, score, kind, "support")
            if score > 0:
                continue
            claim_nums = extract_numbers(claim_norm)
            span_nums = extract_numbers(span_norm)
            neg_diff = negated(claim_norm) != negated(span_norm)
            num_diff = bool(claim_nums) and not numbers_cover(claim_nums, span_nums) and bool(span_nums)
            if neg_diff or num_diff:
                cscore = contradiction_score(claim_norm, span_norm)
                if cscore >= PARTIAL_MIN and (best_conflict is None or cscore > best_conflict.score):
                    best_conflict = make_span(source, anchor, raw, claim_norm, cscore, "contradiction", "contradiction")
        if best_support and best_support.score >= PARTIAL_MIN:
            supports.append(best_support)
        if best_conflict and best_conflict.score >= PARTIAL_MIN:
            contradictions.append(best_conflict)
    return supports, contradictions


def _date_rank(span: Span) -> int:
    if not span.source_date:
        return -1
    year, month, day = span.source_date.split("-")
    return int(year) * 10000 + int(month) * 100 + int(day)


def dated_of(span: Span) -> Dated | None:
    if not span.source_date or not span.source_precision:
        return None
    return Dated(span.source_date, span.source_precision)


def quote_for(span: Span, claim_norm: str) -> str:
    # A conflicting sentence must be quoted whole. Slicing the claim out of
    # "No, the plant exceeded" would hide the word that flips the meaning.
    if span.role != "contradiction":
        sliced = slice_quote(span.raw, claim_norm)
        if sliced:
            return sliced
    text = span.raw.strip()
    if len(text) > 600:
        return text[:597].rstrip() + "..."
    return text


def guard_cell(value: str) -> str:
    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def classify_claim(text: str) -> str:
    if re.search(r"[\"“”«»]", text):
        return "quotation"
    if CAUSAL_RE.search(text):
        return "causal"
    if ATTRIB_RE.search(text):
        return "attribution"
    if re.search(r"\d", text):
        return "quantitative"
    return "paraphrase"


def segment_claims(draft: dict) -> list[dict]:
    if not isinstance(draft, dict) or not isinstance(draft.get("blocks"), list):
        raise AuditError("corpus.json draft is incomplete. Run ingest_draft.py again.")
    claims = []
    for block in draft["blocks"]:
        for sentence in split_sentences(block["text"]):
            words = re.findall(r"\w+", sentence)
            quoted = bool(re.search(r"[\"“”«»]", sentence))
            numbered = bool(re.search(r"\d", sentence))
            if len(words) < 8 and not quoted and not numbered:
                continue
            if sentence.lstrip().startswith("#") and len(words) < 12:
                continue
            claims.append(
                {
                    "id": f"C{len(claims) + 1}",
                    "text": sentence,
                    "type": classify_claim(sentence),
                    "location": block["anchor"],
                }
            )
    if not claims:
        raise AuditError("The draft produced no claim candidates. Write claims.json with one fact per item.")
    return claims


def load_claims(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("claims")
    if not isinstance(payload, list) or not payload:
        raise AuditError("claims.json must contain a non-empty claims list.")
    seen: set[str] = set()
    claims = []
    for index, item in enumerate(payload, 1):
        if not isinstance(item, dict):
            raise AuditError(f"Claim {index} is not an object.")
        text = str(item.get("text", "")).strip()
        if not text:
            raise AuditError(f"Claim {index} has no text.")
        kind = str(item.get("type", "")).strip()
        if kind not in CLAIM_TYPES:
            raise AuditError(
                f"Claim {index} type must be one of {', '.join(CLAIM_TYPES)}."
            )
        cid = str(item.get("id") or f"C{index}")
        if cid in seen:
            raise AuditError(f"Duplicate claim id: {cid}")
        seen.add(cid)
        claims.append(
            {
                "id": cid,
                "text": text,
                "type": kind,
                "location": str(item.get("location") or "unspecified"),
            }
        )
    return claims


def revision_for(verdict: str, quote: str) -> str:
    if verdict == "SUPPORTED":
        return ""
    if verdict == "PARTIAL":
        return f'Tighten the wording to the source span: "{quote}"'
    if verdict == "STALE":
        return f'Replace the claim with the newer source span: "{quote}"'
    if quote:
        return (
            "Sources do not support the claim as written. "
            f'The conflicting source span is: "{quote}"'
        )
    return (
        "No source span scored 0.75 or higher. Delete the claim, soften it, "
        "or add a source that contains it."
    )


def lexical_verdict(span: Span) -> str:
    if span.score >= SUPPORTED_MIN and span.kind in {"exact", "sequence"}:
        return "SUPPORTED"
    return "PARTIAL"


def require_corpus(corpus: dict) -> None:
    if not isinstance(corpus, dict) or not isinstance(corpus.get("draft"), dict):
        raise AuditError("corpus.json has no draft. Run ingest_draft.py first.")
    sources = corpus.get("sources")
    if not isinstance(sources, list):
        raise AuditError("corpus.json has no sources list. Run ingest_draft.py first.")
    draft = corpus["draft"]
    if not isinstance(draft.get("blocks"), list) or "sha256" not in draft or "path" not in draft:
        raise AuditError("corpus.json draft is incomplete. Run ingest_draft.py again.")
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("blocks"), list) or "sha256" not in source:
            raise AuditError("corpus.json has a source without text blocks. Run ingest_draft.py again.")


def verify_claims(corpus: dict, claims: list[dict], claim_source: str) -> dict:
    require_corpus(corpus)
    sources = corpus.get("sources") or []
    if not sources:
        return {
            "certified": False,
            "reason": "No source corpus was supplied. Citation audit declines to certify.",
            "skill": "citation-audit",
            "verifier": VERIFIER_VERSION,
            "claim_source": claim_source,
            "results": [],
            "totals": {"claims": 0, "SUPPORTED": 0, "PARTIAL": 0, "UNSUPPORTED": 0, "STALE": 0},
        }
    results = []
    for claim in claims:
        claim_norm = normalize(claim["text"])
        supports, contradictions = best_spans(claim_norm, sources)
        conflict_pool = list(contradictions)
        for left in supports:
            for right in supports:
                if left.source_sha256 == right.source_sha256:
                    continue
                if numeric_conflict(left.numbers, right.numbers) or left.negated != right.negated:
                    conflict_pool.extend([left, right])
        # Unique by source hash + role + anchor
        dedup: dict[tuple[str, str, str], Span] = {}
        for span in conflict_pool:
            dedup[(span.source_sha256, span.role, span.anchor)] = span
        conflict_pool = list(dedup.values())

        chosen, verdict, note, conflict_quote = decide(claim_norm, supports, conflict_pool)
        quote = ""
        source_name = ""
        source_anchor = ""
        source_sha = ""
        score = 0.0
        kind = ""
        if verdict == "STALE" and conflict_quote is not None:
            quote = quote_for(conflict_quote, claim_norm)
            source_name = conflict_quote.source_name
            source_anchor = conflict_quote.anchor
            source_sha = conflict_quote.source_sha256
            score = chosen.score if chosen else conflict_quote.score
            kind = "stale"
        elif chosen and verdict in {"SUPPORTED", "PARTIAL"}:
            quote = quote_for(chosen, claim_norm)
            source_name = chosen.source_name
            source_anchor = chosen.anchor
            source_sha = chosen.source_sha256
            score = chosen.score
            kind = chosen.kind
        elif verdict == "UNSUPPORTED" and conflict_quote is not None:
            quote = quote_for(conflict_quote, claim_norm)
            source_name = conflict_quote.source_name
            source_anchor = conflict_quote.anchor
            source_sha = conflict_quote.source_sha256
            score = 0.0
            kind = "conflict"
        elif chosen:
            score = chosen.score
            kind = chosen.kind
        if verdict == "PARTIAL":
            note = (note + " " if note else "") + "PARTIAL is string overlap, not entailment."
        results.append(
            {
                "id": claim["id"],
                "text": claim["text"],
                "type": claim["type"],
                "draft_location": claim["location"],
                "verdict": verdict,
                "score": round(float(score), 4),
                "match_kind": kind,
                "quote": quote,
                "source": source_name,
                "source_location": source_anchor,
                "source_sha256": source_sha,
                "revision": revision_for(verdict, quote) if verdict != "SUPPORTED" else "",
                "note": note.strip(),
            }
        )
    results.sort(key=lambda row: (VERDICT_ORDER[row["verdict"]], row["id"]))
    totals = {"claims": len(results), "SUPPORTED": 0, "PARTIAL": 0, "UNSUPPORTED": 0, "STALE": 0}
    for row in results:
        totals[row["verdict"]] += 1
    return {
        "certified": True,
        "reason": "",
        "skill": "citation-audit",
        "verifier": VERIFIER_VERSION,
        "claim_source": claim_source,
        "thresholds": {"supported": SUPPORTED_MIN, "partial": PARTIAL_MIN},
        "results": results,
        "totals": totals,
    }


def decide(
    claim_norm: str, supports: list[Span], conflicts: list[Span]
) -> tuple[Span | None, str, str, Span | None]:
    del claim_norm  # the spans were already scored against the claim
    usable = [span for span in supports if span.score >= PARTIAL_MIN]
    usable.sort(key=lambda span: (-span.score, -_date_rank(span), span.source_name))
    if not usable and not conflicts:
        return None, "UNSUPPORTED", "", None
    if not usable:
        return None, "UNSUPPORTED", "The closest source span disagrees on a number or a negation.", pick_newest(conflicts)

    best = usable[0]
    support_ids = {span.source_sha256 for span in usable}
    disagreeing = []
    internal = []
    for span in conflicts:
        if span.source_sha256 == best.source_sha256 and span.anchor == best.anchor:
            continue
        disagrees = numeric_conflict(span.numbers, best.numbers) or span.negated != best.negated
        if not disagrees:
            continue
        if span.source_sha256 == best.source_sha256:
            internal.append(span)
        elif span.role == "contradiction" and span.source_sha256 in support_ids:
            continue
        else:
            disagreeing.append(span)
    if internal:
        return (
            best,
            "UNSUPPORTED",
            "The matching source also contains a conflicting span.",
            internal[0],
        )
    if not disagreeing:
        return best, lexical_verdict(best), "", None

    dated_best = dated_of(best)
    dated_conflicts = [(span, dated_of(span)) for span in disagreeing]
    dated_conflicts = [(span, when) for span, when in dated_conflicts if when is not None]
    if dated_best is None or not dated_conflicts:
        return (
            best,
            "UNSUPPORTED",
            "Sources disagree and no dated newer source is available to prefer.",
            disagreeing[0],
        )
    newer = [(span, when) for span, when in dated_conflicts if when.strictly_newer_than(dated_best)]
    if newer:
        newest = max(newer, key=lambda item: item[1].iso)[0]
        return (
            best,
            "STALE",
            f"{best.source_name} matches the claim, and {newest.source_name} is newer and disagrees.",
            newest,
        )
    older = [span for span, when in dated_conflicts if dated_best.strictly_newer_than(when)]
    if older and len(older) == len(dated_conflicts):
        names = ", ".join(sorted({span.source_name for span in older}))
        return best, lexical_verdict(best), f"An older source disagrees: {names}.", None
    return (
        best,
        "UNSUPPORTED",
        "Sources disagree and neither date is strictly newer.",
        disagreeing[0],
    )


def pick_newest(spans: list[Span]) -> Span:
    def key(span: Span) -> tuple:
        when = dated_of(span)
        return (when.iso if when else "", span.score, span.source_name)

    return sorted(spans, key=key, reverse=True)[0]


def manifest_for(corpus: dict, claims: list[dict], verdicts: dict) -> dict:
    draft = corpus["draft"]
    claim_blob = canonical_json(claims)
    body = {
        "certified": verdicts["certified"],
        "claim_source": verdicts["claim_source"],
        "claims_sha256": sha256_bytes(claim_blob.encode("utf-8")),
        "draft": {"path": draft["path"], "sha256": draft["sha256"]},
        "reason": verdicts.get("reason", ""),
        "results": verdicts.get("results", []),
        "scope": (
            "Verdicts certify string and number overlap with the supplied corpus only. "
            "The same corpus bytes and the same claims file produce the same verdicts. "
            "A new claim list can change the ledger."
        ),
        "skill": "citation-audit",
        "sources": [
            {
                "date": source.get("date"),
                "date_precision": source.get("date_precision"),
                "path": source["path"],
                "sha256": source["sha256"],
            }
            for source in corpus.get("sources", [])
        ],
        "thresholds": {"partial": PARTIAL_MIN, "supported": SUPPORTED_MIN},
        "totals": verdicts["totals"],
        "verifier": VERIFIER_VERSION,
    }
    return body


def render_html(template: str, verdicts: dict) -> str:
    totals = verdicts["totals"]
    if not verdicts.get("certified", False):
        summary = html.escape(verdicts.get("reason") or "Declined to certify.")
        rows = "<tr><td colspan='9'>No verdicts. A corpus is required.</td></tr>"
        blockers = rows
    else:
        summary = (
            f"{totals['claims']} claims: {totals['SUPPORTED']} SUPPORTED, "
            f"{totals['PARTIAL']} PARTIAL, {totals['UNSUPPORTED']} UNSUPPORTED, "
            f"{totals['STALE']} STALE"
        )
        rows = "".join(row_html(item) for item in verdicts["results"]) or (
            "<tr><td colspan='9'>No claims.</td></tr>"
        )
        blocker_items = [item for item in verdicts["results"] if item["verdict"] != "SUPPORTED"]
        blockers = "".join(row_html(item) for item in blocker_items) or (
            "<tr><td colspan='9'>No blockers.</td></tr>"
        )
    mapping = {
        "{{SUMMARY}}": html.escape(summary) if verdicts.get("certified", False) else summary,
        "{{BLOCKERS}}": blockers,
        "{{ROWS}}": rows,
    }
    # summary for decline is already escaped
    if verdicts.get("certified", False):
        mapping["{{SUMMARY}}"] = html.escape(summary)
    parts = re.split(r"(\{\{[A-Z_]+\}\})", template)
    return "".join(mapping.get(part, part) for part in parts)


def row_html(item: dict) -> str:
    cells = [
        ("", item["id"]),
        ("", item["text"]),
        ("", item["draft_location"]),
        ("", item["type"]),
        ("verdict", item["verdict"]),
        ("", f"{item['score']:.4f}"),
        ("", item["quote"]),
        ("", f"{item['source']} {item['source_location']}".strip()),
        ("", item["revision"]),
    ]
    parts = []
    for css, value in cells:
        attr = f' class="{css}"' if css else ""
        parts.append(f"<td{attr}>{html.escape(str(value))}</td>")
    return "<tr>" + "".join(parts) + "</tr>"


def write_csv(path: Path, verdicts: dict) -> None:
    header = [
        "id",
        "text",
        "draft_location",
        "type",
        "verdict",
        "score",
        "quote",
        "source",
        "source_location",
        "revision",
        "note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        if not verdicts.get("certified", False):
            reason = verdicts.get("reason", "")
            writer.writerow(["", "", "", "", "DECLINED", "", "", "", "", reason, ""])
            return
        for item in verdicts["results"]:
            writer.writerow(
                [
                    guard_cell(str(item[key])) if key != "score" else f"{item['score']:.4f}"
                    for key in header
                ]
            )


def xml_text(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch == "\t" or ch == "\n" or ch == "\r" or ord(ch) >= 32)
    return (
        cleaned.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_xlsx(path: Path, verdicts: dict) -> None:
    header = ["id", "text", "draft_location", "type", "verdict", "score", "quote", "source", "source_location", "revision", "note"]
    rows = [header]
    if not verdicts.get("certified", False):
        rows.append(["", "", "", "", "DECLINED", "", "", "", "", verdicts.get("reason", ""), ""])
    else:
        for item in verdicts["results"]:
            rows.append(
                [
                    guard_cell(str(item["id"])),
                    guard_cell(str(item["text"])),
                    guard_cell(str(item["draft_location"])),
                    guard_cell(str(item["type"])),
                    item["verdict"],
                    f"{item['score']:.4f}",
                    guard_cell(str(item["quote"])),
                    guard_cell(str(item["source"])),
                    guard_cell(str(item["source_location"])),
                    guard_cell(str(item["revision"])),
                    guard_cell(str(item["note"])),
                ]
            )
    sheet_rows = []
    for r, row in enumerate(rows, 1):
        cells = []
        for c, value in enumerate(row, 1):
            ref = f"{column_letter(c)}{r}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{xml_text(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{r}">{"".join(cells)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows)}</sheetData></worksheet>"
    )
    files = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Ledger" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>"
        ),
        "xl/worksheets/sheet1.xml": sheet,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for name in sorted(files):
            package.writestr(name, files[name])


def column_letter(index: int) -> str:
    letters = ""
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def versioned_paths(out_dir: Path) -> dict[str, Path]:
    n = 1
    while True:
        suffix = "" if n == 1 else f"-v{n}"
        paths = {
            "html": out_dir / f"claim-ledger{suffix}.html",
            "csv": out_dir / f"claim-ledger{suffix}.csv",
            "xlsx": out_dir / f"claim-ledger{suffix}.xlsx",
            "manifest": out_dir / f"audit_manifest{suffix}.json",
        }
        if all(not path.exists() for path in paths.values()):
            return paths
        n += 1
        if n > 1000:
            raise AuditError("Could not find a free versioned output name.")


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_template() -> str:
    path = skill_root() / "assets" / "ledger-template.html"
    if not path.is_file():
        raise AuditError(f"Missing ledger template: {path}")
    return path.read_text(encoding="utf-8")
