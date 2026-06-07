from app.pipeline.entity_extractor import extract_all_tickers, extract_tickers_from_text


def test_extract_tickers_from_cashtag() -> None:
    tickers = extract_tickers_from_text("Strong quarter for $NVDA and $AMD")
    assert "NVDA" in tickers
    assert "AMD" in tickers


def test_extract_tickers_from_company_names() -> None:
    tickers = extract_tickers_from_text("Marvel film opens to record box office for Disney")
    assert "DIS" in tickers


def test_extract_all_tickers_merges_metadata_and_text() -> None:
    tickers = extract_all_tickers(
        "Steel tariff discussion heats up",
        {"tickers": ["X", "NUE"], "summary": "United States Steel impacted"},
    )
    assert "X" in tickers
    assert "NUE" in tickers
