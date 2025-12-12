"""
Market regime classification and analysis.

This module provides functionality for classifying market conditions based
on key financial indicators. Uses configurable thresholds to determine
risk-on vs risk-off environments and provides context on USD strength
and yield movements.

The regime classifier analyzes:
- S&P 500 performance (equity market sentiment)
- VIX volatility (fear/complacency indicator)
- DXY dollar index (USD strength/weakness)
- 10-year Treasury yields (interest rate environment)

Classification logic uses JSON-based rules for easy tuning and provides
detailed context for investment decision-making.
"""

import json
from pathlib import Path


def load_regime_config(path: str = "knowledge_base/configs/regime_rules.json") -> dict:
    """
    Load regime classification configuration from JSON file.

    Parameters
    ----------
    path : str, default "knowledge_base/configs/regime_rules.json"
        Path to the JSON configuration file containing regime rules

    Returns
    -------
    dict
        Configuration dictionary with thresholds and labels
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pct_change(a: float | None, b: float | None) -> float | None:
    """
    Calculate percentage change from b to a.

    Parameters
    ----------
    a : float or None
        Current value
    b : float or None
        Base value for comparison

    Returns
    -------
    float or None
        Percentage change from b to a, or None if inputs are missing/invalid
    """
    if a is None or b is None:
        return None
    if b == 0:
        return None
    return ((a - b) / b) * 100.0


def bp_change(a: float | None, b: float | None) -> float | None:
    """
    Calculate basis points change between two values.

    Parameters
    ----------
    a : float or None
        Current value
    b : float or None
        Base value for comparison

    Returns
    -------
    float or None
        Basis points change (a - b) * 100, or None if inputs are missing
    """
    if a is None or b is None:
        return None
    return (a - b) * 100.0


def classify_regime(
    spx_pct: float | None,
    vix_pct: float | None,
    dxy_pct: float | None,
    ust10y_bp: float | None,
    cfg: dict,
) -> dict:
    """
    Classify market regime based on key financial indicators.

    Uses configurable thresholds to determine risk-on vs risk-off environments
    and provides context on USD strength and yield movements.

    Parameters
    ----------
    spx_pct : float or None
        S&P 500 percentage change
    vix_pct : float or None
        VIX volatility percentage change
    dxy_pct : float or None
        DXY dollar index percentage change
    ust10y_bp : float or None
        10-year Treasury yield change in basis points
    cfg : dict
        Configuration dictionary with thresholds and labels

    Returns
    -------
    dict
        Classification result with keys: regime, usd_context, yields, note
    """
    labels = cfg["labels"]
    th = cfg["thresholds"]
    tb = cfg["tie_breakers"]

    if spx_pct is None or vix_pct is None:
        return {
            "regime": labels["risk_off"],
            "usd_context": "n/a",
            "yields": "n/a",
            "note": "Insufficient signals to confirm risk-on.",
        }

    risk_on = (spx_pct >= th["risk_on"]["spx_pct_min"]) and (
        vix_pct <= th["risk_on"]["vix_pct_max"]
    )
    if not risk_on:
        return {
            "regime": labels["risk_off"],
            "usd_context": "n/a",
            "yields": "n/a",
            "note": "Stocks/VIX not confirming risk appetite.",
        }

    usd_soft = None
    usd_context = labels["usd_firm"]
    if dxy_pct is not None:
        usd_soft = dxy_pct <= th["usd_soft"]["dxy_pct_max"]
        usd_context = labels["usd_soft"] if usd_soft else labels["usd_firm"]

    yields_label = labels["yields_mixed"]
    if ust10y_bp is not None:
        yields_label = (
            labels["yields_rising"]
            if ust10y_bp >= th["yields_rising"]["ust10y_bp_min"]
            else labels["yields_mixed"]
        )

    if dxy_pct is not None and (
        spx_pct >= tb["us_exceptionalism"]["spx_min"]
        and dxy_pct >= tb["us_exceptionalism"]["dxy_min"]
    ):
        usd_context = labels["usd_usx"]

    return {
        "regime": labels["risk_on"],
        "usd_context": usd_context,
        "yields": yields_label,
        "note": "Falling VIX and rising stocks confirm risk-on; "
        "USD/yields provide sector bias context.",
    }
