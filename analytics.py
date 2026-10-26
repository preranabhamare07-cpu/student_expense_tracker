"""
analytics.py
------------
Pure-Python analytics layer for the Student Expense Tracker.

Responsibilities:
  - Accept raw expense data (list of dicts from database.py) and a monthly
    allowance value.
  - Compute summary statistics, trends, and per-category breakdowns using
    Pandas.
  - Build ready-to-render Plotly figures that app.py can display directly.
  - No database calls or Streamlit imports here — this module is stateless
    and easy to unit-test in isolation.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Palette & shared style ────────────────────────────────────────────────────
CATEGORY_COLORS: dict[str, str] = {
    "Food":          "#FF6B6B",
    "Travel":        "#4ECDC4",
    "Education":     "#45B7D1",
    "Shopping":      "#96CEB4",
    "Entertainment": "#FFEAA7",
    "Bills":         "#DDA0DD",
    "Other":         "#98D8C8",
}

_PLOT_BG = "rgba(0,0,0,0)"        # transparent — lets Streamlit theme show through
_PAPER_BG = "rgba(0,0,0,0)"
_FONT_COLOR = "#E0E0E0"
_GRID_COLOR = "rgba(255,255,255,0.08)"

_BASE_LAYOUT = dict(
    paper_bgcolor=_PAPER_BG,
    plot_bgcolor=_PLOT_BG,
    font=dict(color=_FONT_COLOR, family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


# ── Data preparation ──────────────────────────────────────────────────────────
def build_dataframe(expenses: list[dict]) -> pd.DataFrame:
    """
    Convert the list-of-dicts returned by database.py into a typed DataFrame.

    Columns guaranteed to be present:
        id, date (datetime64), amount (float), category (str),
        payment_method (str), notes (str), month_label (str "YYYY-MM"),
        week (int ISO week), day_of_week (str).
    """
    if not expenses:
        return pd.DataFrame(
            columns=["id", "date", "amount", "category",
                     "payment_method", "notes", "month_label", "week", "day_of_week"]
        )

    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["notes"] = df["notes"].fillna("")
    df["month_label"] = df["date"].dt.strftime("%Y-%m")
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.day_name()
    df.sort_values("date", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ── Summary statistics ─────────────────────────────────────────────────────────
def compute_summary(df: pd.DataFrame, allowance: float) -> dict:
    """
    Return a dict of high-level KPIs.

    Keys
    ----
    total_spent        : float  — sum of all amounts in the DataFrame.
    remaining_budget   : float  — allowance minus total_spent.
    budget_used_pct    : float  — 0–100 percentage of allowance consumed.
    avg_daily_spend    : float  — mean spend per unique day with any expense.
    largest_expense    : float  — single highest amount.
    transaction_count  : int    — number of rows.
    top_category       : str    — category with highest cumulative spend.
    """
    if df.empty:
        return {
            "total_spent": 0.0,
            "remaining_budget": allowance,
            "budget_used_pct": 0.0,
            "avg_daily_spend": 0.0,
            "largest_expense": 0.0,
            "transaction_count": 0,
            "top_category": "—",
        }

    total = df["amount"].sum()
    remaining = allowance - total
    pct = (total / allowance * 100) if allowance > 0 else 0.0
    daily_avg = df.groupby("date")["amount"].sum().mean()
    top_cat = df.groupby("category")["amount"].sum().idxmax()

    return {
        "total_spent": round(total, 2),
        "remaining_budget": round(remaining, 2),
        "budget_used_pct": round(pct, 1),
        "avg_daily_spend": round(daily_avg, 2),
        "largest_expense": round(df["amount"].max(), 2),
        "transaction_count": len(df),
        "top_category": top_cat,
    }


def compute_category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame with columns [category, total, pct] sorted by total desc.
    """
    if df.empty:
        return pd.DataFrame(columns=["category", "total", "pct"])

    grouped = (
        df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total"})
    )
    grand_total = grouped["total"].sum()
    grouped["pct"] = (grouped["total"] / grand_total * 100).round(1)
    return grouped.sort_values("total", ascending=False).reset_index(drop=True)


def compute_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return monthly totals: columns [month_label, total].
    """
    if df.empty:
        return pd.DataFrame(columns=["month_label", "total"])

    monthly = (
        df.groupby("month_label")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total"})
        .sort_values("month_label")
    )
    return monthly


def compute_payment_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Return [payment_method, total, pct] sorted by total desc."""
    if df.empty:
        return pd.DataFrame(columns=["payment_method", "total", "pct"])

    grouped = (
        df.groupby("payment_method")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total"})
    )
    grand = grouped["total"].sum()
    grouped["pct"] = (grouped["total"] / grand * 100).round(1)
    return grouped.sort_values("total", ascending=False).reset_index(drop=True)


# ── Plotly figures ─────────────────────────────────────────────────────────────
def fig_category_pie(df: pd.DataFrame) -> go.Figure:
    """Donut chart — spending share per category."""
    breakdown = compute_category_breakdown(df)

    if breakdown.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False,
                           font=dict(color=_FONT_COLOR, size=14))
        fig.update_layout(**_BASE_LAYOUT, title="Spending by Category")
        return fig

    colors = [CATEGORY_COLORS.get(c, "#AAAAAA") for c in breakdown["category"]]

    fig = go.Figure(
        go.Pie(
            labels=breakdown["category"],
            values=breakdown["total"],
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="#1a1a2e", width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.2f}<br>%{percent}<extra></extra>",
        )
    )
    fig.update_layout(**_BASE_LAYOUT, title="Spending by Category")
    return fig


def fig_monthly_bar(df: pd.DataFrame, allowance: float) -> go.Figure:
    """Bar chart of monthly totals with an optional allowance reference line."""
    monthly = compute_monthly_trend(df)

    if monthly.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False,
                           font=dict(color=_FONT_COLOR, size=14))
        fig.update_layout(**_BASE_LAYOUT, title="Monthly Spending Trend")
        return fig

    fig = go.Figure(
        go.Bar(
            x=monthly["month_label"],
            y=monthly["total"],
            marker=dict(
                color=monthly["total"],
                colorscale="Tealrose",
                showscale=False,
                line=dict(width=0),
            ),
            hovertemplate="<b>%{x}</b><br>₹%{y:,.2f}<extra></extra>",
            name="Spent",
        )
    )

    if allowance > 0:
        fig.add_hline(
            y=allowance,
            line_dash="dash",
            line_color="#FFD700",
            annotation_text=f"Allowance ₹{allowance:,.0f}",
            annotation_font_color="#FFD700",
        )

    fig.update_layout(
        **_BASE_LAYOUT,
        title="Monthly Spending Trend",
        xaxis=dict(gridcolor=_GRID_COLOR, title="Month"),
        yaxis=dict(gridcolor=_GRID_COLOR, title="Amount (₹)"),
    )
    return fig


def fig_daily_line(df: pd.DataFrame) -> go.Figure:
    """Cumulative daily spend line chart for the most recent 30 days."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False,
                           font=dict(color=_FONT_COLOR, size=14))
        fig.update_layout(**_BASE_LAYOUT, title="Daily Spending (Last 30 Days)")
        return fig

    cutoff = df["date"].max() - pd.Timedelta(days=29)
    recent = df[df["date"] >= cutoff].copy()
    daily = (
        recent.groupby("date")["amount"].sum().reset_index().sort_values("date")
    )

    fig = go.Figure(
        go.Scatter(
            x=daily["date"],
            y=daily["amount"],
            mode="lines+markers",
            line=dict(color="#4ECDC4", width=2.5),
            marker=dict(size=6, color="#4ECDC4"),
            fill="tozeroy",
            fillcolor="rgba(78,205,196,0.12)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>₹%{y:,.2f}<extra></extra>",
            name="Daily",
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        title="Daily Spending (Last 30 Days)",
        xaxis=dict(gridcolor=_GRID_COLOR, title="Date"),
        yaxis=dict(gridcolor=_GRID_COLOR, title="Amount (₹)"),
    )
    return fig


def fig_payment_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart — spending by payment method."""
    breakdown = compute_payment_breakdown(df)

    if breakdown.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data yet", showarrow=False,
                           font=dict(color=_FONT_COLOR, size=14))
        fig.update_layout(**_BASE_LAYOUT, title="Spending by Payment Method")
        return fig

    fig = go.Figure(
        go.Bar(
            x=breakdown["total"],
            y=breakdown["payment_method"],
            orientation="h",
            marker=dict(
                color=breakdown["total"],
                colorscale="Purples",
                showscale=False,
            ),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        title="Spending by Payment Method",
        xaxis=dict(gridcolor=_GRID_COLOR, title="Amount (₹)"),
        yaxis=dict(gridcolor=_GRID_COLOR),
    )
    return fig


def fig_category_trend(df: pd.DataFrame) -> go.Figure:
    """Stacked area chart — category spending month over month."""
    if df.empty or df["month_label"].nunique() < 2:
        fig = go.Figure()
        fig.add_annotation(text="Need at least 2 months of data", showarrow=False,
                           font=dict(color=_FONT_COLOR, size=14))
        fig.update_layout(**_BASE_LAYOUT, title="Category Trends Over Time")
        return fig

    pivot = (
        df.groupby(["month_label", "category"])["amount"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("month_label")
    )

    fig = go.Figure()
    for cat in pivot.columns[1:]:
        fig.add_trace(
            go.Scatter(
                x=pivot["month_label"],
                y=pivot[cat],
                mode="lines",
                stackgroup="one",
                name=cat,
                line=dict(width=0.5),
                fillcolor=CATEGORY_COLORS.get(cat, "#AAAAAA"),
                hovertemplate=f"<b>{cat}</b><br>%{{x}}<br>₹%{{y:,.2f}}<extra></extra>",
            )
        )

    fig.update_layout(
        **_BASE_LAYOUT,
        title="Category Trends Over Time",
        xaxis=dict(gridcolor=_GRID_COLOR, title="Month"),
        yaxis=dict(gridcolor=_GRID_COLOR, title="Amount (₹)"),
    )
    return fig
