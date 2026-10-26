# Student Expense Tracker 💸

A clean, data-driven expense tracking application built for students — powered by **Python**, **Streamlit**, **SQLite**, **Pandas**, and **Plotly**.

---

## Features (Phase 1)

| Feature | Details |
|---|---|
| **Add expenses** | Date, amount, category, payment method, optional notes |
| **Categories** | Food · Travel · Education · Shopping · Entertainment · Bills · Other |
| **Payment methods** | Cash · UPI · Debit Card · Credit Card · Net Banking · Other |
| **Monthly allowance** | Set and update your budget; live progress bar shows usage |
| **KPI dashboard** | Total spent, remaining budget, % used, daily average, largest expense |
| **5 interactive charts** | Category donut, monthly bar, daily line, payment bar, category trend |
| **Filterable table** | Filter by category, payment method, or month |
| **Delete expenses** | Remove any entry by ID |
| **Persistent storage** | SQLite database (`expenses.db`) — no external services needed |

---

## Project Structure

```
Student_Expense_Tracker/
│
├── app.py           # Streamlit UI — entry-point, layout, and form handling
├── database.py      # SQLite layer — schema, CRUD, allowance settings
├── analytics.py     # Pandas stats + Plotly chart factories (no DB/UI imports)
├── model.py         # ML stub — Phase 2 placeholder (scikit-learn)
├── requirements.txt # Python dependencies
└── README.md        # This file
```

### File Responsibilities

**`database.py`**
- Owns the SQLite connection and schema (`expenses` + `settings` tables).
- All queries are parameterised — no string interpolation.
- Exports: `init_db`, `add_expense`, `get_all_expenses`, `get_expenses_by_month`, `update_expense`, `delete_expense`, `get_monthly_allowance`, `set_monthly_allowance`.

**`analytics.py`**
- Stateless module — takes data in, returns DataFrames and Plotly figures.
- No database calls or Streamlit imports.
- Exports: `build_dataframe`, `compute_summary`, `compute_category_breakdown`, `compute_monthly_trend`, `compute_payment_breakdown`, and five `fig_*` chart functions.

**`model.py`**
- Safe stub for Phase 2 ML features.
- Currently exports: `is_model_ready` (→ `False`), `predict_next_month` (→ `None`), `detect_anomalies` (→ empty DataFrame).
- Phase 2 will add budget forecasting, anomaly detection, and category classification.

**`app.py`**
- Streamlit entry-point — imports from all three modules above.
- Handles all UI rendering, form validation messages, and page state.
- Contains no raw SQL or chart-building logic.

---

## Setup & Running

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

The SQLite database file (`expenses.db`) is created automatically on the first run.

---

## Database Schema

### `expenses` table

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-incremented |
| `date` | TEXT | ISO-8601 (`YYYY-MM-DD`) |
| `amount` | REAL | Always positive |
| `category` | TEXT | One of the 7 supported categories |
| `payment_method` | TEXT | One of the 6 supported methods |
| `notes` | TEXT | Optional free-text, default `''` |

### `settings` table

| Column | Type | Notes |
|---|---|---|
| `key` | TEXT PK | Setting name (e.g. `monthly_allowance`) |
| `value` | TEXT | Stored as string, cast on read |

---

## Roadmap

- [x] Phase 1 — Core CRUD, analytics dashboard, persistent storage
- [ ] Phase 2 — ML: budget forecast, anomaly detection, note-based category suggestion
- [ ] Phase 3 — Export to CSV/PDF, multi-month comparison, mobile layout polish

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11+ | Runtime |
| Streamlit | Web UI framework |
| SQLite | Local persistent storage |
| Pandas | Data wrangling |
| Plotly | Interactive charts |
| scikit-learn | ML (Phase 2) |
