# WHY: Extract ticker symbols from news metadata and article text.

from __future__ import annotations

import re

TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
CASHTAG_RE = re.compile(r"\b([A-Z]{1,5})\b")

COMPANY_ALIASES: dict[str, list[str]] = {
    "NVDA": ["nvidia", "nvda"],
    "AMD": ["amd", "advanced micro"],
    "INTC": ["intel", "intc"],
    "AAPL": ["apple", "aapl"],
    "MSFT": ["microsoft", "msft"],
    "GOOGL": ["google", "alphabet", "googl"],
    "META": ["meta", "facebook"],
    "TSLA": ["tesla", "tsla"],
    "DIS": ["disney", "marvel"],
    "NKE": ["nike", "nke"],
    "X": ["us steel", "united states steel"],
    "NUE": ["nucor"],
    "STLD": ["steel dynamics"],
    "CLF": ["cleveland-cliffs", "cleveland cliffs"],
    "LMT": ["lockheed"],
    "RTX": ["raytheon", "rtx"],
    "SMCI": ["super micro", "supermicro"],
    "AVGO": ["broadcom", "avgo"],
}

VALID_TICKERS = set(COMPANY_ALIASES.keys())


def extract_tickers_from_metadata(metadata: dict) -> list[str]:
    tickers: list[str] = []
    raw = metadata.get("tickers") or metadata.get("related_tickers") or []
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(",") if t.strip()]
    for ticker in raw:
        normalized = str(ticker).upper().strip()
        if normalized and normalized not in tickers:
            tickers.append(normalized)
    return tickers


def extract_tickers_from_text(text: str) -> list[str]:
    tickers: list[str] = []
    for match in TICKER_RE.findall(text):
        if match in VALID_TICKERS and match not in tickers:
            tickers.append(match)

    lowered = text.lower()
    for ticker, aliases in COMPANY_ALIASES.items():
        if any(alias in lowered for alias in aliases) and ticker not in tickers:
            tickers.append(ticker)
    return tickers


def extract_all_tickers(title: str, metadata: dict | None = None) -> list[str]:
    metadata = metadata or {}
    tickers = extract_tickers_from_metadata(metadata)
    for ticker in extract_tickers_from_text(title):
        if ticker not in tickers:
            tickers.append(ticker)
    summary = metadata.get("summary", "")
    if summary:
        for ticker in extract_tickers_from_text(summary):
            if ticker not in tickers:
                tickers.append(ticker)
    return tickers
