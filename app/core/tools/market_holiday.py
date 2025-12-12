"""
US market holiday checker tool for trading schedule analysis.

This module provides functionality to check US market holidays and trading
schedules using a comprehensive holiday database. It supports various query
types including specific date checks, yearly holiday listings, and finding
remaining holidays in the current year.

The tool integrates with LangChain's tool framework to provide market
calendar information for financial analysis and trading planning applications.

Key features:
- Specific date holiday verification
- Complete yearly holiday listings
- Remaining holidays calculation
- Market closure impact analysis
- NYSE and NASDAQ holiday coverage
"""

import json
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class HolidayInput(BaseModel):
    """Input for market holiday checker tool."""

    query: Optional[str] = Field(
        default=None,
        description=(
            "Holiday query. Can be:\n"
            "• Specific date (YYYY-MM-DD) to check if it's a holiday\n"
            "• 'all 2025' or 'holidays 2025' for all holidays in a year\n"
            "• 'remaining 2025' or 'left 2025' for remaining holidays this year\n"
            "• Leave empty to check if today is a holiday"
        ),
    )


@tool(args_schema=HolidayInput)
def market_holiday_checker(query: str = None) -> str:
    """
    **MARKET CALENDAR**: Check US market holidays and trading schedules.

    Use this for:
    • Checking if a specific date is a market holiday
    • Getting all market holidays for a year
    • Finding remaining holidays in the current year
    • Planning around market closures and trading schedules
    """
    holidays_path = Path("knowledge_base/semistatic/us_market_holidays.json")

    try:
        holiday_data = json.loads(holidays_path.read_text())
        today = datetime.now()
        current_year = today.year
        if query is None:
            date_str = today.strftime("%Y-%m-%d")
            return _check_single_date(date_str, holiday_data, current_year)

        query_lower = query.lower()
        year_match = None
        for year in range(2020, 2030):
            if str(year) in query:
                year_match = year
                break

        if year_match is None:
            year_match = current_year

        if any(word in query_lower for word in ["all", "list", "holidays"]):
            return _list_all_holidays(year_match, holiday_data)
        elif any(word in query_lower for word in ["remaining", "left", "upcoming"]):
            return _list_remaining_holidays(year_match, holiday_data, today)
        elif _is_date_format(query):
            return _check_single_date(query, holiday_data, year_match)
        else:
            return _list_all_holidays(year_match, holiday_data)

    except Exception as e:
        logging.error(f"Error in market_holiday_checker: {str(e)}")
        return f"Unable to access holiday information. Error: {str(e)}"


def _is_date_format(date_str: str) -> bool:
    """Check if string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        logging.error(f"Date format error for string: {date_str}")
        return False


def _check_single_date(date_str: str, holiday_data: dict, year: int) -> str:
    """Check if a specific date is a holiday."""
    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d")
        for holiday in holiday_data.get("holidays", []):
            holiday_date_str = f"{year} {holiday['date']}"
            try:
                holiday_date = datetime.strptime(holiday_date_str, "%Y %b %d")
                if check_date.date() == holiday_date.date():
                    return (
                        f"**{date_str}** is a US market holiday: **{holiday['name']}**. "
                        f"Markets are closed."
                    )
            except ValueError:
                logging.error(f"Date parsing error for holiday: {holiday_date_str}")
                continue
        for early_close in holiday_data.get("early_closes", []):
            early_close_date_str = f"{year} {early_close['date']}"
            try:
                early_close_date = datetime.strptime(early_close_date_str, "%Y %b %d")
                if check_date.date() == early_close_date.date():
                    return (
                        f"**{date_str}** is an early close day: "
                        f"**{early_close['name']}**. "
                        f"Markets close at {early_close['close_time']}."
                    )
            except ValueError:
                logging.error(
                    f"Date parsing error for early close: {early_close_date_str}"
                )
                continue

        return f"**{date_str}** is a regular trading day. US markets are open."

    except ValueError:
        logging.error(f"Invalid date format provided: {date_str}")
        return f"Invalid date format: {date_str}. Please use YYYY-MM-DD format."


def _list_all_holidays(year: int, holiday_data: dict) -> str:
    """List all holidays for a specific year."""
    year_holidays = []
    for holiday in holiday_data.get("holidays", []):
        holiday_date_str = f"{year} {holiday['date']}"
        try:
            date_obj = datetime.strptime(holiday_date_str, "%Y %b %d")
            year_holidays.append((date_obj, holiday["name"], "Market Closed"))
        except ValueError:
            logging.error(f"Date parsing error for holiday: {holiday_date_str}")
            continue

    for early_close in holiday_data.get("early_closes", []):
        early_close_date_str = f"{year} {early_close['date']}"
        try:
            date_obj = datetime.strptime(early_close_date_str, "%Y %b %d")
            close_info = f"Early Close ({early_close['close_time']})"
            year_holidays.append((date_obj, early_close["name"], close_info))
        except ValueError:
            logging.error(f"Date parsing error for early close: {early_close_date_str}")
            continue

    if not year_holidays:
        return f"No market holidays found for {year}."

    year_holidays.sort(key=lambda x: x[0])

    result = [f"**US Market Holidays for {year}:**\n"]

    for i, (date_obj, holiday_name, status) in enumerate(year_holidays, 1):
        day_name = date_obj.strftime("%A")
        date_formatted = date_obj.strftime("%B %d")
        result.append(
            f"{i}. **{holiday_name}** - {day_name}, {date_formatted} ({status})"
        )

    total_closed = sum(1 for _, _, status in year_holidays if "Market Closed" in status)
    total_early = len(year_holidays) - total_closed

    result.append(
        f"\n📅 Total: {total_closed} market closures, "
        f"{total_early} early closes in {year}"
    )
    return "\n".join(result)


def _list_remaining_holidays(year: int, holiday_data: dict, today: datetime) -> str:
    """List remaining holidays for the year."""
    remaining_holidays = []

    for holiday in holiday_data.get("holidays", []):
        holiday_date_str = f"{year} {holiday['date']}"
        try:
            date_obj = datetime.strptime(holiday_date_str, "%Y %b %d")
            if date_obj.date() >= today.date():
                remaining_holidays.append((date_obj, holiday["name"], "Market Closed"))
        except ValueError:
            logging.error(f"Date parsing error for holiday: {holiday_date_str}")
            continue

    for early_close in holiday_data.get("early_closes", []):
        early_close_date_str = f"{year} {early_close['date']}"
        try:
            date_obj = datetime.strptime(early_close_date_str, "%Y %b %d")
            if date_obj.date() >= today.date():
                close_info = f"Early Close ({early_close['close_time']})"
                remaining_holidays.append((date_obj, early_close["name"], close_info))
        except ValueError:
            logging.error(f"Date parsing error for early close: {early_close_date_str}")
            continue

    if not remaining_holidays:
        return f"No remaining market holidays for {year}."

    remaining_holidays.sort(key=lambda x: x[0])

    result = [f"**Remaining US Market Holidays for {year}:**\n"]

    for i, (date_obj, holiday_name, status) in enumerate(remaining_holidays, 1):
        day_name = date_obj.strftime("%A")
        date_formatted = date_obj.strftime("%B %d")
        days_until = (date_obj.date() - today.date()).days
        if days_until == 0:
            time_info = "Today"
        elif days_until == 1:
            time_info = "Tomorrow"
        else:
            time_info = f"in {days_until} days"

        result.append(
            f"{i}. **{holiday_name}** - {day_name}, {date_formatted} "
            f"({status}, {time_info})"
        )

    total_closed = sum(
        1 for _, _, status in remaining_holidays if "Market Closed" in status
    )
    total_early = len(remaining_holidays) - total_closed

    result.append(
        f"\n📅 {total_closed} market closures, {total_early} early closes "
        f"remaining in {year}"
    )
    return "\n".join(result)
