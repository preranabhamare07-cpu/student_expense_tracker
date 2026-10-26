"""
app.py
------
Streamlit entry-point for the Student Expense Tracker.

Responsibilities:
  - Bootstrap the database on first run.
  - Render the sidebar (allowance settings + add-expense form).
  - Render the main area: KPI cards, charts from analytics.py, and
    the editable expenses table.
  - Delegate all DB calls to database.py and all chart/stat work to
    analytics.py. This file contains *only* UI logic.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import datetime
from typing import Optional

import pandas as pd
import streamlit as st

import analytics
import database as db
import model

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Expense Tracker",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — dark glassmorphism theme ─────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ───────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a4e 50%, #24243e 100%);
        min-height: 100vh;
    }

    /* ── Sidebar ──────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* ── KPI cards ────────────────────────────────────────────── */
    .kpi-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 8px;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(78, 205, 196, 0.15);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 500;
        color: rgba(255,255,255,0.55);
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #4ECDC4;
        line-height: 1.1;
    }
    .kpi-value.danger  { color: #FF6B6B; }
    .kpi-value.warning { color: #FFEAA7; }
    .kpi-value.neutral { color: #E0E0E0; }

    /* ── Section headings ─────────────────────────────────────── */
    .section-heading {
        font-size: 1.1rem;
        font-weight: 600;
        color: rgba(255,255,255,0.85);
        margin: 24px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ── Budget progress bar ──────────────────────────────────── */
    .budget-bar-wrapper {
        background: rgba(255,255,255,0.08);
        border-radius: 99px;
        height: 10px;
        overflow: hidden;
        margin: 6px 0 14px 0;
    }
    .budget-bar-fill {
        height: 100%;
        border-radius: 99px;
        transition: width 0.5s ease;
    }

    /* ── Streamlit overrides ──────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #4ECDC4, #45B7D1);
        color: #0f0c29;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        transition: opacity 0.2s ease, transform 0.15s ease;
    }
    .stButton > button:hover {
        opacity: 0.88;
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] label {
        color: rgba(255,255,255,0.6) !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #4ECDC4 !important;
        font-size: 1.4rem !important;
    }

    .stDataFrame { border-radius: 12px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Bootstrap ─────────────────────────────────────────────────────────────────
@st.cache_resource
def _init():
    """Initialise the database exactly once per app session."""
    db.init_db()


_init()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _kpi(label: str, value: str, css_class: str = "") -> None:
    css = f"kpi-value {css_class}".strip()
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="{css}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _budget_bar(pct: float) -> None:
    clamped = min(pct, 100)
    if pct >= 90:
        color = "#FF6B6B"
    elif pct >= 70:
        color = "#FFEAA7"
    else:
        color = "#4ECDC4"
    st.markdown(
        f"""
        <div class="budget-bar-wrapper">
            <div class="budget-bar-fill"
                 style="width:{clamped}%; background:{color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(icon: str, title: str) -> None:
    st.markdown(
        f'<div class="section-heading">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💸 Expense Tracker")
    st.markdown("---")

    # ── Monthly Allowance ──────────────────────────────────────────────────
    _section("🎯", "Monthly Allowance")
    current_allowance = db.get_monthly_allowance()
    new_allowance = st.number_input(
        "Set allowance (₹)",
        min_value=0.0,
        value=float(current_allowance),
        step=500.0,
        format="%.2f",
        key="allowance_input",
        help="Your total budget for the current month.",
    )
    if st.button("💾 Save Allowance", key="save_allowance_btn"):
        try:
            db.set_monthly_allowance(new_allowance)
            st.success("Allowance updated!")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

    st.markdown("---")

    # ── Add Expense ────────────────────────────────────────────────────────
    _section("➕", "Add Expense")

    with st.form("add_expense_form", clear_on_submit=True):
        exp_date = st.date_input(
            "Date",
            value=datetime.date.today(),
            max_value=datetime.date.today(),
            key="exp_date",
        )
        exp_amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            max_value=1_000_000.0,
            value=100.0,
            step=10.0,
            format="%.2f",
            key="exp_amount",
        )
        exp_category = st.selectbox("Category", db.CATEGORIES, key="exp_cat")
        exp_method = st.selectbox("Payment Method", db.PAYMENT_METHODS, key="exp_method")
        exp_notes = st.text_input("Notes (optional)", max_chars=200, key="exp_notes")

        submitted = st.form_submit_button("Add Expense ➕")
        if submitted:
            try:
                new_id = db.add_expense(
                    expense_date=exp_date,
                    amount=exp_amount,
                    category=exp_category,
                    payment_method=exp_method,
                    notes=exp_notes,
                )
                st.success(f"Expense #{new_id} added!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.markdown("---")
    st.caption("Student Expense Tracker v1.0 · ML features coming soon 🚀")


# ── Load data ─────────────────────────────────────────────────────────────────
all_expenses = db.get_all_expenses()
allowance = db.get_monthly_allowance()
df_all = analytics.build_dataframe(all_expenses)

# Current-month slice for budget KPIs
today = datetime.date.today()
current_month_expenses = db.get_expenses_by_month(today.year, today.month)
df_month = analytics.build_dataframe(current_month_expenses)
summary = analytics.compute_summary(df_month, allowance)


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#E0E0E0; font-size:2rem; margin-bottom:0;'>"
    "💸 Student Expense Tracker"
    "</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:rgba(255,255,255,0.45); margin-top:4px;'>"
    f"Tracking your finances · {today.strftime('%B %Y')}"
    "</p>",
    unsafe_allow_html=True,
)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
_section("📊", "This Month at a Glance")
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    _kpi("Total Spent", f"₹{summary['total_spent']:,.0f}")
with k2:
    rem_class = "danger" if summary["remaining_budget"] < 0 else ""
    _kpi("Remaining", f"₹{summary['remaining_budget']:,.0f}", rem_class)
with k3:
    pct = summary["budget_used_pct"]
    pct_class = "danger" if pct >= 90 else ("warning" if pct >= 70 else "")
    _kpi("Budget Used", f"{pct:.1f}%", pct_class)
with k4:
    _kpi("Avg Daily", f"₹{summary['avg_daily_spend']:,.0f}", "neutral")
with k5:
    _kpi("Largest Expense", f"₹{summary['largest_expense']:,.0f}", "neutral")
with k6:
    _kpi("Transactions", str(summary["transaction_count"]), "neutral")

# Budget progress bar
if allowance > 0:
    _budget_bar(summary["budget_used_pct"])
    st.caption(
        f"₹{summary['total_spent']:,.2f} of ₹{allowance:,.2f} allowance used "
        f"({summary['budget_used_pct']}%)"
    )

# ── Charts ────────────────────────────────────────────────────────────────────
_section("📈", "Spending Analysis")

row1_left, row1_right = st.columns([1, 1])

with row1_left:
    st.plotly_chart(
        analytics.fig_category_pie(df_all),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with row1_right:
    st.plotly_chart(
        analytics.fig_monthly_bar(df_all, allowance),
        use_container_width=True,
        config={"displayModeBar": False},
    )

row2_left, row2_right = st.columns([1, 1])

with row2_left:
    st.plotly_chart(
        analytics.fig_daily_line(df_all),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with row2_right:
    st.plotly_chart(
        analytics.fig_payment_bar(df_all),
        use_container_width=True,
        config={"displayModeBar": False},
    )

# Stacked area chart (full-width)
if df_all["month_label"].nunique() >= 2 if not df_all.empty else False:
    st.plotly_chart(
        analytics.fig_category_trend(df_all),
        use_container_width=True,
        config={"displayModeBar": False},
    )

# ── Expense Table ─────────────────────────────────────────────────────────────
_section("🗒️", "All Expenses")

# ── Filters ───────────────────────────────────────────────────────────────────
if not df_all.empty:
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])

    with f_col1:
        cat_options = ["All"] + sorted(df_all["category"].unique().tolist())
        selected_cat = st.selectbox("Filter by Category", cat_options, key="filter_cat")

    with f_col2:
        method_options = ["All"] + sorted(df_all["payment_method"].unique().tolist())
        selected_method = st.selectbox("Filter by Payment", method_options, key="filter_method")

    with f_col3:
        month_options = ["All"] + sorted(df_all["month_label"].unique().tolist(), reverse=True)
        selected_month = st.selectbox("Filter by Month", month_options, key="filter_month")

    df_view = df_all.copy()
    if selected_cat != "All":
        df_view = df_view[df_view["category"] == selected_cat]
    if selected_method != "All":
        df_view = df_view[df_view["payment_method"] == selected_method]
    if selected_month != "All":
        df_view = df_view[df_view["month_label"] == selected_month]

    display_df = df_view[["id", "date", "amount", "category", "payment_method", "notes"]].copy()
    display_df["date"] = display_df["date"].dt.strftime("%d %b %Y")
    display_df.columns = ["ID", "Date", "Amount (₹)", "Category", "Payment", "Notes"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount (₹)": st.column_config.NumberColumn(format="₹%.2f"),
        },
    )
    st.caption(f"Showing {len(df_view)} of {len(df_all)} expense(s).")
else:
    st.info(
        "No expenses recorded yet. Use the **Add Expense** form in the sidebar to get started!",
        icon="💡",
    )

# ── Delete Expense ─────────────────────────────────────────────────────────────
if not df_all.empty:
    _section("🗑️", "Delete an Expense")
    with st.form("delete_form"):
        del_id = st.number_input(
            "Expense ID to delete",
            min_value=1,
            step=1,
            key="del_id",
            help="Enter the ID shown in the table above.",
        )
        del_submitted = st.form_submit_button("Delete ❌")
        if del_submitted:
            deleted = db.delete_expense(int(del_id))
            if deleted:
                st.success(f"Expense #{int(del_id)} deleted.")
                st.rerun()
            else:
                st.error(f"No expense found with ID {int(del_id)}.")

# ── ML Teaser ─────────────────────────────────────────────────────────────────
if not model.is_model_ready(df_all):
    st.info(
        "🤖 **ML features are coming in Phase 2!** Keep adding expenses — "
        "once you have 3+ months of data, the app will offer budget forecasts "
        "and anomaly detection.",
        icon="🚀",
    )
