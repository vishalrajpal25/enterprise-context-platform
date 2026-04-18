"""Fiscal calendar resolver.

Resolves canonical time identifiers (`last_quarter`, `current_quarter`,
`year_to_date`, etc.) to absolute date ranges relative to the *current wall
clock*, using a fiscal year start month from the calendar config asset.

This is the difference between a screenshot demo (frozen dates in seed data)
and a touch-and-feel demo (always live, always correct).

Output shape is the contract consumed by src/semantic/cube_executor.py:
    {
        "dimension": "Revenue.date",
        "range": ["2025-10-01", "2025-12-31"],
        "label": "Q3-FY2026",
        "fiscal_year": "FY2026",
        "fiscal_quarter": "Q3",
        "resolved_at": "2026-04-06T...",
    }
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


DEFAULT_DIMENSION = "Revenue.date"


@dataclass(frozen=True)
class FiscalContext:
    fiscal_year_start_month: int  # 1..12
    fiscal_year_label: str = "FY{end_year}"
    dimension: str = DEFAULT_DIMENSION

    @classmethod
    def from_calendar_asset(cls, content: dict[str, Any] | None) -> "FiscalContext":
        if not content:
            return cls(fiscal_year_start_month=1)
        return cls(
            fiscal_year_start_month=int(content.get("fiscal_year_start_month", 1)),
            fiscal_year_label=str(content.get("fiscal_year_label", "FY{end_year}")),
            dimension=str(content.get("dimension", DEFAULT_DIMENSION)),
        )


def _fy_for(d: date, start_month: int) -> int:
    """Return the fiscal year *end calendar year* for a given date.

    A fiscal year that starts in April and runs through March has end year =
    calendar year of its March. So April 2025 → FY2026.
    """
    if start_month == 1:
        return d.year
    return d.year + 1 if d.month >= start_month else d.year


def _quarter_index(d: date, start_month: int) -> int:
    """Return fiscal quarter index 1..4 for the date."""
    months_into_fy = (d.month - start_month) % 12
    return months_into_fy // 3 + 1


def _quarter_bounds(fy_end_year: int, q_index: int, start_month: int) -> tuple[date, date]:
    """Return [start, end] inclusive dates for the given fiscal Q within FY.

    A quarter spans 3 calendar months. The end is the last day of the third
    month, computed as (first day of the fourth month) - 1 day.
    """
    fy_start_calendar_year = fy_end_year if start_month == 1 else fy_end_year - 1
    q_start_month_absolute = start_month + (q_index - 1) * 3  # 1..12 + (..)
    year_offset, month0 = divmod(q_start_month_absolute - 1, 12)
    start = date(fy_start_calendar_year + year_offset, month0 + 1, 1)

    # First day of the month AFTER the quarter ends.
    next_month_index = month0 + 3  # zero-based across all months
    next_year = start.year + next_month_index // 12
    next_month = next_month_index % 12 + 1
    end = date(next_year, next_month, 1) - timedelta(days=1)
    return start, end


def _format_label(fy_end_year: int, q_index: int, label_template: str) -> tuple[str, str]:
    fy_label = label_template.format(end_year=fy_end_year)
    return fy_label, f"Q{q_index}"


def resolve(
    time_id: str,
    fiscal: FiscalContext,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Resolve a canonical time identifier to an absolute date range.

    Returns None for unknown identifiers — caller decides how to handle that
    (orchestrator currently passes the resolved concept through unchanged so
    Cube execution will skip the time filter rather than crash).
    """
    today = (now or datetime.utcnow()).date()
    sm = fiscal.fiscal_year_start_month
    label_template = fiscal.fiscal_year_label

    if time_id == "current_quarter":
        fy = _fy_for(today, sm)
        q = _quarter_index(today, sm)
    elif time_id == "last_quarter":
        # Step back 3 months from the start of the current quarter, then re-derive.
        cur_fy = _fy_for(today, sm)
        cur_q = _quarter_index(today, sm)
        if cur_q == 1:
            fy = cur_fy - 1
            q = 4
        else:
            fy = cur_fy
            q = cur_q - 1
    elif time_id in ("current_year", "this_year", "year_to_date"):
        fy = _fy_for(today, sm)
        start, _ = _quarter_bounds(fy, 1, sm)
        end = today if time_id == "year_to_date" else _quarter_bounds(fy, 4, sm)[1]
        fy_label, _ = _format_label(fy, 1, label_template)
        return {
            "dimension": fiscal.dimension,
            "range": [start.isoformat(), end.isoformat()],
            "label": f"{fy_label} ({'YTD' if time_id == 'year_to_date' else 'full year'})",
            "fiscal_year": fy_label,
            "fiscal_quarter": None,
            "resolved_at": (now or datetime.utcnow()).isoformat(),
        }
    elif time_id == "last_year":
        fy = _fy_for(today, sm) - 1
        start, _ = _quarter_bounds(fy, 1, sm)
        _, end = _quarter_bounds(fy, 4, sm)
        fy_label, _ = _format_label(fy, 1, label_template)
        return {
            "dimension": fiscal.dimension,
            "range": [start.isoformat(), end.isoformat()],
            "label": f"{fy_label} (full year)",
            "fiscal_year": fy_label,
            "fiscal_quarter": None,
            "resolved_at": (now or datetime.utcnow()).isoformat(),
        }
    elif time_id == "month_to_date":
        start = date(today.year, today.month, 1)
        return {
            "dimension": fiscal.dimension,
            "range": [start.isoformat(), today.isoformat()],
            "label": f"{today.strftime('%b %Y')} (MTD)",
            "fiscal_year": label_template.format(end_year=_fy_for(today, sm)),
            "fiscal_quarter": f"Q{_quarter_index(today, sm)}",
            "resolved_at": (now or datetime.utcnow()).isoformat(),
        }
    else:
        # Handle absolute quarter references (e.g., q4_2019 → fiscal Q4 of CY2019)
        m_abs = re.match(r"q(\d)_(\d{4})", time_id)
        if m_abs:
            q_index = int(m_abs.group(1))
            calendar_year = int(m_abs.group(2))
            # Compute the fiscal year that contains this calendar quarter.
            # For fiscal start April: calendar Q4 (Oct-Dec) is in FY that ends
            # next year, calendar Q1 (Jan-Mar) is in the FY ending this year.
            # Use the first month of the calendar quarter to derive fy.
            cal_month = (q_index - 1) * 3 + 1  # Q1→Jan, Q2→Apr, Q3→Jul, Q4→Oct
            ref_date = date(calendar_year, cal_month, 1)
            fy = _fy_for(ref_date, sm)
            fq = _quarter_index(ref_date, sm)
            start, end = _quarter_bounds(fy, fq, sm)
            fy_label, q_label = _format_label(fy, fq, label_template)
            return {
                "dimension": fiscal.dimension,
                "range": [start.isoformat(), end.isoformat()],
                "label": f"{q_label}-{fy_label} (calendar Q{q_index} {calendar_year})",
                "fiscal_year": fy_label,
                "fiscal_quarter": q_label,
                "resolved_at": (now or datetime.utcnow()).isoformat(),
            }

        # Handle "last_N_quarters" pattern (e.g., last_8_quarters)
        m = re.match(r"last_(\d+)_quarters?", time_id)
        if m:
            n = int(m.group(1))
            # End of the most recent completed quarter
            cur_fy = _fy_for(today, sm)
            cur_q = _quarter_index(today, sm)
            # Step back to last completed quarter
            if cur_q == 1:
                end_fy, end_q = cur_fy - 1, 4
            else:
                end_fy, end_q = cur_fy, cur_q - 1
            _, end_date = _quarter_bounds(end_fy, end_q, sm)

            # Walk back N-1 more quarters to find start
            start_fy, start_q = end_fy, end_q
            for _ in range(n - 1):
                if start_q == 1:
                    start_fy -= 1
                    start_q = 4
                else:
                    start_q -= 1
            start_date, _ = _quarter_bounds(start_fy, start_q, sm)

            start_fy_label = label_template.format(end_year=start_fy)
            end_fy_label = label_template.format(end_year=end_fy)
            return {
                "dimension": fiscal.dimension,
                "range": [start_date.isoformat(), end_date.isoformat()],
                "label": f"Last {n} quarters (Q{start_q}-{start_fy_label} to Q{end_q}-{end_fy_label})",
                "fiscal_year": end_fy_label,
                "fiscal_quarter": f"Q{end_q}",
                "resolved_at": (now or datetime.utcnow()).isoformat(),
            }
        return None

    start, end = _quarter_bounds(fy, q, sm)
    fy_label, q_label = _format_label(fy, q, label_template)
    return {
        "dimension": fiscal.dimension,
        "range": [start.isoformat(), end.isoformat()],
        "label": f"{q_label}-{fy_label}",
        "fiscal_year": fy_label,
        "fiscal_quarter": q_label,
        "resolved_at": (now or datetime.utcnow()).isoformat(),
    }
