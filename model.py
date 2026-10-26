"""
model.py
--------
Machine-learning layer for the Student Expense Tracker.

This module is a **stub** — the scaffolding is in place so the rest of the
app can import from it safely, but the actual ML implementation will be added
in a later phase.

Planned features (Phase 2):
  - Spending anomaly detection (Isolation Forest or Z-score).
  - Monthly budget forecast (Linear Regression / ARIMA).
  - Category classification from expense notes (TF-IDF + Logistic Regression).
  - Over-budget early-warning alerts.

Current exports (safe to call, return placeholder values):
  - predict_next_month(df)  → None
  - detect_anomalies(df)    → empty DataFrame
  - is_model_ready(df)      → False
"""

from __future__ import annotations

import pandas as pd


def is_model_ready(df: pd.DataFrame) -> bool:
    """
    Return True when there is enough historical data to train the ML model.

    Threshold (Phase 2): at least 3 months of recorded expenses.
    Currently always returns False (stub).
    """
    return False


def predict_next_month(df: pd.DataFrame) -> None:
    """
    Predict total spending for the next calendar month.

    Parameters
    ----------
    df : DataFrame produced by analytics.build_dataframe()

    Returns
    -------
    None (stub) — will return a float in Phase 2.
    """
    # TODO (Phase 2): fit LinearRegression on monthly totals and forecast.
    return None


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag unusually large individual expenses.

    Parameters
    ----------
    df : DataFrame produced by analytics.build_dataframe()

    Returns
    -------
    Empty DataFrame (stub) — will return rows with an 'anomaly_score' column
    in Phase 2.
    """
    # TODO (Phase 2): apply IsolationForest from scikit-learn.
    return pd.DataFrame()
