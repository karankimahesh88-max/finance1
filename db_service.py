"""
Mock DB service — stores everything in st.session_state (in-memory only).
Data resets every time the Streamlit server restarts. Swap for a real
Firestore-backed version later if needed.
"""
import uuid
from datetime import date, timedelta

import pandas as pd
import streamlit as st

CATEGORIES = [
    "Salary", "Freelance", "Groceries", "Rent", "Utilities",
    "Transport", "Entertainment", "Dining Out", "Healthcare",
    "Shopping", "Travel", "Other",
]


def _store():
    if "mock_db" not in st.session_state:
        st.session_state.mock_db = {
            "transactions": _seed_transactions(),
            "investments": _seed_investments(),
            "goals": _seed_goals(),
            "accounts": _seed_accounts(),
            "credit_cards": _seed_credit_cards(),
            "budgets": _seed_budgets(),
            "debts": _seed_debts(),
            "scheduled": _seed_scheduled(),
            "preferences": {"currency": "INR", "darkMode": False, "widgetOrder": []},
        }
    return st.session_state.mock_db


def _seed_transactions():
    today = date.today()
    rows = [
        {"id": str(uuid.uuid4()), "type": "income", "category": "Salary",
         "description": "Monthly salary", "amount": 75000,
         "date": (today.replace(day=1)).isoformat()},
        {"id": str(uuid.uuid4()), "type": "expense", "category": "Rent",
         "description": "Apartment rent", "amount": 18000,
         "date": (today - timedelta(days=20)).isoformat()},
        {"id": str(uuid.uuid4()), "type": "expense", "category": "Groceries",
         "description": "Supermarket run", "amount": 3200,
         "date": (today - timedelta(days=12)).isoformat()},
        {"id": str(uuid.uuid4()), "type": "expense", "category": "Dining Out",
         "description": "Dinner with friends", "amount": 1500,
         "date": (today - timedelta(days=7)).isoformat()},
        {"id": str(uuid.uuid4()), "type": "expense", "category": "Transport",
         "description": "Fuel", "amount": 2200,
         "date": (today - timedelta(days=3)).isoformat()},
    ]
    return rows


def _seed_investments():
    return [
        {"id": str(uuid.uuid4()), "symbol": "AAPL", "quantity": 10,
         "purchasePrice": 150.0, "date": (date.today() - timedelta(days=200)).isoformat()},
        {"id": str(uuid.uuid4()), "symbol": "MSFT", "quantity": 5,
         "purchasePrice": 300.0, "date": (date.today() - timedelta(days=100)).isoformat()},
    ]


def _seed_goals():
    return [
        {"id": str(uuid.uuid4()), "title": "Emergency fund", "targetAmount": 100000,
         "currentAmount": 42000, "deadline": (date.today() + timedelta(days=180)).isoformat()},
    ]


def _seed_accounts():
    return [
        {"id": str(uuid.uuid4()), "name": "Wallet", "type": "Cash", "balance": 4500},
        {"id": str(uuid.uuid4()), "name": "Bank account", "type": "Bank", "balance": 135374},
    ]


def _seed_credit_cards():
    return [
        {"id": str(uuid.uuid4()), "name": "Credit card", "limit": 100000,
         "amountDue": 24900, "billingStart": date.today().replace(day=1).isoformat(),
         "billingEnd": (date.today().replace(day=1) + timedelta(days=30)).isoformat()},
    ]


def _seed_budgets():
    today = date.today()
    return [
        {"id": str(uuid.uuid4()), "category": "Entertainment", "period": "weekly",
         "limitAmount": 3000, "startDate": (today - timedelta(days=today.weekday())).isoformat(),
         "endDate": (today - timedelta(days=today.weekday()) + timedelta(days=6)).isoformat()},
        {"id": str(uuid.uuid4()), "category": "Dining Out", "period": "monthly",
         "limitAmount": 10000, "startDate": today.replace(day=1).isoformat(),
         "endDate": (today.replace(day=1) + timedelta(days=30)).isoformat()},
    ]


def _seed_debts():
    return [
        {"id": str(uuid.uuid4()), "type": "debt", "counterparty": "Frank",
         "totalAmount": 30000, "paidAmount": 10000,
         "dueDate": (date.today() + timedelta(days=40)).isoformat()},
        {"id": str(uuid.uuid4()), "type": "credit", "counterparty": "Sam",
         "totalAmount": 3000, "paidAmount": 0,
         "dueDate": (date.today() + timedelta(days=20)).isoformat()},
    ]


def _seed_scheduled():
    today = date.today()
    return [
        {"id": str(uuid.uuid4()), "description": "Netflix", "category": "Entertainment",
         "amount": 1400, "type": "expense", "isSubscription": True, "recurrence": "monthly",
         "nextDate": (today + timedelta(days=8)).isoformat()},
        {"id": str(uuid.uuid4()), "description": "Spotify", "category": "Entertainment",
         "amount": 1200, "type": "expense", "isSubscription": True, "recurrence": "monthly",
         "nextDate": (today + timedelta(days=3)).isoformat()},
        {"id": str(uuid.uuid4()), "description": "Electricity bill", "category": "Utilities",
         "amount": 14500, "type": "expense", "isSubscription": False, "recurrence": "monthly",
         "nextDate": (today + timedelta(days=14)).isoformat()},
    ]


# ---------------- Transactions ----------------
def get_transactions(uid: str) -> pd.DataFrame:
    rows = _store()["transactions"]
    if not rows:
        return pd.DataFrame(columns=["id", "type", "category", "description", "amount", "date"])
    df = pd.DataFrame(rows)
    return df.sort_values("date", ascending=False).reset_index(drop=True)


def add_transaction(uid, amount, category, tx_type, description, tx_date):
    _store()["transactions"].append({
        "id": str(uuid.uuid4()), "type": tx_type, "category": category,
        "description": description, "amount": amount, "date": tx_date,
    })


def update_transaction(uid, tx_id, **fields):
    for row in _store()["transactions"]:
        if row["id"] == tx_id:
            row.update(fields)


def delete_transaction(uid, tx_id):
    _store()["transactions"] = [r for r in _store()["transactions"] if r["id"] != tx_id]


# ---------------- Investments ----------------
def get_investments(uid: str) -> pd.DataFrame:
    rows = _store()["investments"]
    if not rows:
        return pd.DataFrame(columns=["id", "symbol", "quantity", "purchasePrice", "date"])
    return pd.DataFrame(rows)


def add_investment(uid, symbol, quantity, purchase_price, purchase_date):
    _store()["investments"].append({
        "id": str(uuid.uuid4()), "symbol": symbol.upper(), "quantity": quantity,
        "purchasePrice": purchase_price, "date": purchase_date,
    })


def delete_investment(uid, inv_id):
    _store()["investments"] = [r for r in _store()["investments"] if r["id"] != inv_id]


# ---------------- Goals ----------------
def get_goals(uid: str) -> pd.DataFrame:
    rows = _store()["goals"]
    if not rows:
        return pd.DataFrame(columns=["id", "title", "targetAmount", "currentAmount", "deadline"])
    return pd.DataFrame(rows)


def add_goal(uid, title, target, deadline):
    _store()["goals"].append({
        "id": str(uuid.uuid4()), "title": title, "targetAmount": target,
        "currentAmount": 0, "deadline": deadline,
    })


def update_goal_progress(uid, goal_id, new_amount):
    for row in _store()["goals"]:
        if row["id"] == goal_id:
            row["currentAmount"] = new_amount


def delete_goal(uid, goal_id):
    _store()["goals"] = [r for r in _store()["goals"] if r["id"] != goal_id]


# ---------------- Preferences ----------------
def get_preferences(uid: str) -> dict:
    return _store()["preferences"]


def update_preferences(uid, darkMode=False, currency="INR", widgetOrder=None):
    _store()["preferences"] = {
        "darkMode": darkMode, "currency": currency, "widgetOrder": widgetOrder or [],
    }


# ---------------- Accounts ----------------
def get_accounts(uid: str) -> pd.DataFrame:
    rows = _store()["accounts"]
    if not rows:
        return pd.DataFrame(columns=["id", "name", "type", "balance"])
    return pd.DataFrame(rows)


def add_account(uid, name, acc_type, balance):
    _store()["accounts"].append({
        "id": str(uuid.uuid4()), "name": name, "type": acc_type, "balance": float(balance),
    })


def update_account_balance(uid, acc_id, new_balance):
    for row in _store()["accounts"]:
        if row["id"] == acc_id:
            row["balance"] = float(new_balance)


def delete_account(uid, acc_id):
    _store()["accounts"] = [r for r in _store()["accounts"] if r["id"] != acc_id]


# ---------------- Credit cards ----------------
def get_credit_cards(uid: str) -> pd.DataFrame:
    rows = _store()["credit_cards"]
    if not rows:
        return pd.DataFrame(columns=["id", "name", "limit", "amountDue", "billingStart", "billingEnd"])
    return pd.DataFrame(rows)


def add_credit_card(uid, name, limit, amount_due, billing_start, billing_end):
    _store()["credit_cards"].append({
        "id": str(uuid.uuid4()), "name": name, "limit": float(limit),
        "amountDue": float(amount_due), "billingStart": billing_start, "billingEnd": billing_end,
    })


def update_credit_card_due(uid, card_id, amount_due):
    for row in _store()["credit_cards"]:
        if row["id"] == card_id:
            row["amountDue"] = float(amount_due)


def delete_credit_card(uid, card_id):
    _store()["credit_cards"] = [r for r in _store()["credit_cards"] if r["id"] != card_id]


# ---------------- Budgets ----------------
def get_budgets(uid: str) -> pd.DataFrame:
    rows = _store()["budgets"]
    if not rows:
        return pd.DataFrame(columns=["id", "category", "period", "limitAmount", "startDate", "endDate"])
    return pd.DataFrame(rows)


def add_budget(uid, category, period, limit_amount, start_date, end_date):
    _store()["budgets"].append({
        "id": str(uuid.uuid4()), "category": category, "period": period,
        "limitAmount": float(limit_amount), "startDate": start_date, "endDate": end_date,
    })


def delete_budget(uid, budget_id):
    _store()["budgets"] = [r for r in _store()["budgets"] if r["id"] != budget_id]


def budget_spent(uid: str, category: str, start_date: str, end_date: str) -> float:
    """Sum of expense transactions in a category within a date range."""
    df = get_transactions(uid)
    if df.empty:
        return 0.0
    mask = (
        (df["type"] == "expense") & (df["category"] == category)
        & (df["date"] >= start_date) & (df["date"] <= end_date)
    )
    return float(df.loc[mask, "amount"].sum())


# ---------------- Debts & Credits ----------------
def get_debts(uid: str) -> pd.DataFrame:
    rows = _store()["debts"]
    if not rows:
        return pd.DataFrame(columns=["id", "type", "counterparty", "totalAmount", "paidAmount", "dueDate"])
    return pd.DataFrame(rows)


def add_debt(uid, debt_type, counterparty, total_amount, due_date, paid_amount=0):
    _store()["debts"].append({
        "id": str(uuid.uuid4()), "type": debt_type, "counterparty": counterparty,
        "totalAmount": float(total_amount), "paidAmount": float(paid_amount), "dueDate": due_date,
    })


def update_debt_paid(uid, debt_id, paid_amount):
    for row in _store()["debts"]:
        if row["id"] == debt_id:
            row["paidAmount"] = float(paid_amount)


def delete_debt(uid, debt_id):
    _store()["debts"] = [r for r in _store()["debts"] if r["id"] != debt_id]


# ---------------- Scheduled transactions & subscriptions ----------------
def get_scheduled(uid: str) -> pd.DataFrame:
    rows = _store()["scheduled"]
    if not rows:
        return pd.DataFrame(columns=["id", "description", "category", "amount", "type",
                                      "isSubscription", "recurrence", "nextDate"])
    df = pd.DataFrame(rows)
    return df.sort_values("nextDate").reset_index(drop=True)


def add_scheduled(uid, description, category, amount, tx_type, is_subscription, recurrence, next_date):
    _store()["scheduled"].append({
        "id": str(uuid.uuid4()), "description": description, "category": category,
        "amount": float(amount), "type": tx_type, "isSubscription": is_subscription,
        "recurrence": recurrence, "nextDate": next_date,
    })


def delete_scheduled(uid, sched_id):
    _store()["scheduled"] = [r for r in _store()["scheduled"] if r["id"] != sched_id]
