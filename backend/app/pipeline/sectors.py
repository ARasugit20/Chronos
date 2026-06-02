TICKER_SECTORS: dict[str, str] = {
    "NKE": "consumer",
    "ADDYY": "consumer",
    "MAR": "travel",
    "UAL": "travel",
    "KO": "consumer",
    "DIS": "media",
    "CMCSA": "media",
    "NFLX": "media",
    "QQQ": "tech",
    "TLT": "fixed_income",
    "GLD": "commodities",
    "SPY": "broad_market",
    "FOX": "media",
    "PEP": "consumer",
    "BUD": "consumer",
}


def ticker_sector(ticker: str) -> str:
    return TICKER_SECTORS.get(ticker, "general")
