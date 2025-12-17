"""
Market data retrieval and analysis services.

This module provides comprehensive market data functionality for the
market intelligence application. It interfaces with external data
sources like Yahoo Finance and FRED to retrieve real-time and
historical market information.

Key capabilities:
- Real-time price data for stocks, ETFs, and indices
- Sector performance analysis and ETF mapping
- Market snapshot generation with key indicators
- Individual ticker analysis with fundamentals
- Historical data retrieval with configurable periods
- Market regime indicator calculation
- Sector strength ranking and comparison

Data sources:
- Yahoo Finance (yfinance) for price and volume data
- FRED API for economic indicators
- Local JSON configuration for sector mappings

The module uses caching to improve performance and includes error
handling for robust data retrieval in production environments.
"""

import os
import logging
import json
import pandas as pd
import yfinance as yf
from fredapi import Fred
from functools import lru_cache
from pathlib import Path
import streamlit as st
from typing import Literal
from core.analyzers.regime import pct_change, bp_change


@lru_cache(maxsize=1)
def load_sector_data() -> dict:
    """
    Load sector representative data from configuration file.

    Returns
    -------
    dict
        Sector to representative ticker mapping, empty dict if loading fails
    """
    sector_file = (
        Path(__file__).parent.parent.parent
        / "knowledge_base"
        / "semistatic"
        / "sector_representatives.json"
    )
    try:
        with open(sector_file, "r") as f:
            data = json.load(f)
            return data.get("sector_representatives.json", {})
    except Exception as e:
        logging.warning(f"Warning: Could not load sector data: {e}")
        return {}


@lru_cache(maxsize=1)
def load_market_indicators() -> dict:
    """
    Load market indicator tickers from configuration file.

    Returns
    -------
    dict
        Market indicator to ticker mapping, empty dict if loading fails
    """
    indicators_file = (
        Path(__file__).parent.parent.parent
        / "knowledge_base"
        / "semistatic"
        / "market_indicators.json"
    )
    try:
        with open(indicators_file, "r") as f:
            data = json.load(f)
            return data.get("market_indicators", {})
    except Exception as e:
        logging.warning(f"Warning: Could not load market indicators: {e}")
        return {}


def get_sector_etfs() -> list[str]:
    """Get list of all sector ETF symbols from JSON file."""
    sector_data = load_sector_data()
    return list(sector_data.keys())


@st.cache_data(ttl=900)
def get_index_snap(tickers: list, period: str, interval: str = "1d") -> pd.DataFrame:
    df = yf.download(tickers, period=period, interval=interval, auto_adjust=True)[
        "Close"
    ].ffill()
    return df


@st.cache_data(ttl=1800)
def get_sector_perf(period="1wk") -> "pd.DataFrame":
    sectors = get_sector_etfs()
    df = yf.download(sectors, period=period, interval="1d", auto_adjust=True)[
        "Close"
    ].ffill()
    start_prices = df.iloc[0]
    end_prices = df.iloc[-1]
    perf = (end_prices / start_prices - 1).sort_values(ascending=False)

    result_df = perf.to_frame("return").assign(sector=perf.index)
    result_df["start_price"] = start_prices[result_df["sector"]].values
    result_df["end_price"] = end_prices[result_df["sector"]].values
    result_df["start_date"] = df.index[0].strftime("%Y-%m-%d")
    result_df["end_date"] = df.index[-1].strftime("%Y-%m-%d")

    return result_df.reset_index(drop=True)


@st.cache_data(ttl=900)
def _get_price_data(ticker: str, period: str = "1wk") -> dict[str, float | None | str]:
    """
    Get comprehensive price data for a ticker with a single API call.
    """
    try:
        data = yf.download(
            ticker, period=period, interval="1d", auto_adjust=True, progress=False
        )
        if data.empty:
            logging.warning(
                f"Warning: No data returned for ticker {ticker} with period {period}"
            )
            return {
                "latest_close": None,
                "latest_date": None,
                "past_close": None,
                "past_date": None,
                "source": "Yahoo",
                "error": "No data returned from Yahoo Finance",
            }

        series = data["Close"].sort_index(ascending=True)
        latest_val = float(series.iloc[-1][ticker])
        past_val = float(series.iloc[0][ticker])
        latest_date = series.index[-1].date()
        past_date = series.index[0].date()
        return {
            "latest_close": round(latest_val, 4),
            "latest_date": latest_date,
            "past_close": round(past_val, 4),
            "past_date": past_date,
            "source": "Yahoo",
        }
    except Exception as e:
        logging.error(f"Error in _get_price_data for {ticker}: {str(e)}")
        return {
            "latest_close": None,
            "latest_date": None,
            "past_close": None,
            "past_date": None,
            "source": "Yahoo",
            "error": str(e),
        }


@st.cache_data(ttl=1800)
def _get_yield_data(
    analysis_period: Literal["1wk", "1mo", "3mo", "6mo", "1y"] = "1wk",
) -> dict[str, float | None | str]:
    """
    Get both current and historical 10Y yield from FRED.
    """
    window_days = (
        5
        if analysis_period == "1wk"
        else (
            21
            if analysis_period == "1mo"
            else (
                63
                if analysis_period == "3mo"
                else 126 if analysis_period == "6mo" else 252
            )
        )
    )
    fred_key = os.getenv("FRED_API_KEY", "")
    if fred_key:
        try:
            fred = Fred(api_key=fred_key)
            series = fred.get_series("DGS10").dropna().sort_index(ascending=True)
            if len(series) > window_days:
                return {
                    "latest_yield": float(series.iloc[-1]),
                    "latest_date": series.index[-1].date(),
                    "past_yield": float(series.iloc[-(window_days)]),
                    "past_date": series.index[-(window_days)].date(),
                    "source": "FRED",
                }

        except Exception:
            logging.error("Error fetching yield data from FRED.")
            return {
                "latest_yield": None,
                "latest_date": None,
                "past_yield": None,
                "past_date": None,
                "source": "FRED",
            }


@st.cache_data(ttl=900)
def get_market_snapshot(period: str) -> dict:
    """
    Returns latest levels and short-window deltas for core market indicators.
    - spx_pct, vix_pct, dxy_pct, gold_pct as %
    - ust10y_bp as basis points
    Sources prefer FRED for 10Y; fall back to Yahoo's ^TNX.
    """
    market_data = {}
    tickers = ["^GSPC", "^VIX", "DX-Y.NYB", "GC=F"]
    for ticker in tickers:
        market_data[ticker] = _get_price_data(ticker, period)

    spx_data = market_data["^GSPC"]
    spx_now = spx_data["latest_close"]
    spx_then = spx_data["past_close"]

    vix_data = market_data["^VIX"]
    vix_now = vix_data["latest_close"]
    vix_then = vix_data["past_close"]

    dxy_data = market_data["DX-Y.NYB"]
    dxy_now = dxy_data["latest_close"]
    dxy_then = dxy_data["past_close"]

    gold_data = market_data["GC=F"]
    gold_now = gold_data["latest_close"]
    gold_then = gold_data["past_close"]
    start_date = end_date = None

    for data in market_data.values():
        if data["latest_date"] and data["past_date"]:
            start_date = data["past_date"].strftime("%Y-%m-%d")
            end_date = data["latest_date"].strftime("%Y-%m-%d")
            break

    yield_data = _get_yield_data(period)
    if yield_data and yield_data["latest_yield"]:
        ust10y_latest = yield_data["latest_yield"]
        ust10y_then = yield_data["past_yield"]
        yield_source = yield_data["source"]
    else:
        ust10y_latest = ust10y_then = yield_source = None
    spx_pct = pct_change(spx_now, spx_then)
    vix_pct = pct_change(vix_now, vix_then)
    dxy_pct = pct_change(dxy_now, dxy_then)
    gold_pct = pct_change(gold_now, gold_then)
    ust10y_bp = bp_change(ust10y_latest, ust10y_then)

    return {
        "levels": {
            "spx": spx_now,
            "vix": vix_now,
            "dxy": dxy_now,
            "gold": gold_now,
            "ust10y": ust10y_latest,
        },
        "previous_levels": {
            "spx": spx_then,
            "vix": vix_then,
            "dxy": dxy_then,
            "gold": gold_then,
            "ust10y": ust10y_then,
        },
        "deltas": {
            "spx_pct": spx_pct,
            "vix_pct": vix_pct,
            "dxy_pct": dxy_pct,
            "gold_pct": gold_pct,
            "ust10y_bp": ust10y_bp,
        },
        "dates": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "analysis_period": period,
        "source": {
            "yields": yield_source,
        },
    }


def get_ticker_samples() -> dict[str, list[str]]:
    """Get representative ticker samples for each sector ETF."""
    sector_data = load_sector_data()
    samples = {}

    for etf_symbol, etf_data in sector_data.items():
        if "stocks" in etf_data:
            stock_tickers = list(etf_data["stocks"].keys())[:5]
            samples[etf_symbol] = stock_tickers

    return samples


def get_sector_etf_mapping(source: str = None) -> dict[str, str]:
    """Get mapping from Yahoo Finance sector names to ETF symbols."""
    sector_data = load_sector_data()
    if source == "yahoo":
        attribute = "yahoo_sector_name"
    else:
        attribute = "sector_name"
    mapping = {}
    for etf_symbol, etf_data in sector_data.items():
        if attribute in etf_data:
            sector_name = etf_data[attribute]
            mapping[sector_name] = etf_symbol

    return mapping


@st.cache_data(ttl=1800)
def get_ticker_info(ticker: str, period: str = "1wk") -> dict:
    """
    Get ticker data and compare to S&P 500 and its sector.
    Uses consistent 1-week analysis period by default for alignment with other tools.
    """
    try:
        stock = yf.Ticker(ticker)

        info = stock.info
        sector = info.get("sector", "Unknown")
        company_name = info.get("longName", ticker)

        ticker_data = _get_price_data(ticker, period)

        if not ticker_data["latest_close"]:
            error_detail = ticker_data.get("error", "Unknown error")
            logging.warning(f"No price data available for {ticker}: {error_detail}")

        latest_price = ticker_data["latest_close"]
        past_price = ticker_data["past_close"]
        ticker_return = ((latest_price / past_price) - 1) * 100 if past_price else 0

        spx_data = _get_price_data("^GSPC", period)
        spx_return = (
            ((spx_data["latest_close"] / spx_data["past_close"]) - 1) * 100
            if spx_data["latest_close"] and spx_data["past_close"]
            else 0
        )

        sector_etf_map = get_sector_etf_mapping("yahoo")
        sector_etf = sector_etf_map.get(sector, "XLK")
        sector_data = _get_price_data(sector_etf, period)
        sector_return = (
            ((sector_data["latest_close"] / sector_data["past_close"]) - 1) * 100
            if sector_data["latest_close"] and sector_data["past_close"]
            else 0
        )
        try:
            hist = stock.history(period=period, auto_adjust=True)
            spx_hist = yf.Ticker("^GSPC").history(period=period, auto_adjust=True)
            sector_hist = yf.Ticker(sector_etf).history(period=period, auto_adjust=True)

            comparison_df = pd.DataFrame(
                {
                    ticker: hist["Close"],
                    "S&P 500": spx_hist["Close"],
                    f"{sector_etf} ({sector})": sector_hist["Close"],
                }
            )

            period_high = hist["High"].max() if not hist.empty else latest_price
            period_low = hist["Low"].min() if not hist.empty else latest_price
        except Exception:
            comparison_df = None
            period_high = period_low = latest_price

        return {
            "ticker": ticker,
            "company_name": company_name,
            "sector": sector,
            "sector_etf": sector_etf,
            "period": period,
            "ticker_return": ticker_return,
            "spx_return": spx_return,
            "sector_return": sector_return,
            "comparison_data": comparison_df,
            "outperformance_vs_spx": ticker_return - spx_return,
            "outperformance_vs_sector": ticker_return - sector_return,
            "current_price": latest_price,
            "period_high": period_high,
            "period_low": period_low,
        }

    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {str(e)}")
        raise ValueError(f"Error fetching data for {ticker}: {str(e)}")


@st.cache_data(ttl=3600)
def get_ticker_fundamentals(ticker: str) -> dict:
    """
    Get basic fundamental metrics for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "dividend_yield": (
                info.get("dividendYield", 0) * 100
                if info.get("dividendYield")
                else "N/A"
            ),
            "beta": info.get("beta", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
        }
    except Exception as e:
        logging.error(f"Error fetching fundamentals for {ticker}: {str(e)}")
        return {"error": str(e)}
