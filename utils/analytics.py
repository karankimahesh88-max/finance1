"""Simple analytics helpers operating on the transactions DataFrame."""
import pandas as pd


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    exp = df[df["type"] == "expense"]
    if exp.empty:
        return exp
    return exp.groupby("category", as_index=False)["amount"].sum()


def monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["month"] = d["date"].dt.to_period("M").astype(str)
    grouped = d.groupby(["month", "type"], as_index=False)["amount"].sum()
    return grouped


def generate_insights(df: pd.DataFrame, portfolio_growth) -> list:
    tips = []
    if df.empty:
        return ["Add some transactions to see personalized insights here."]

    income = df.loc[df["type"] == "income", "amount"].sum()
    expense = df.loc[df["type"] == "expense", "amount"].sum()

    if income > 0:
        savings_ratio = (income - expense) / income * 100
        if savings_ratio < 0:
            tips.append("You're spending more than you earn this period — worth a closer look.")
        elif savings_ratio < 20:
            tips.append(f"You're saving about {savings_ratio:.0f}% of income — try aiming for 20%+.")
        else:
            tips.append(f"Nice! You're saving about {savings_ratio:.0f}% of your income.")

    exp_by_cat = category_breakdown(df)
    if not exp_by_cat.empty:
        top_cat = exp_by_cat.sort_values("amount", ascending=False).iloc[0]
        tips.append(f"Your biggest expense category is {top_cat['category']}.")

    if portfolio_growth is not None:
        if portfolio_growth >= 0:
            tips.append(f"Your portfolio is up {portfolio_growth:.1f}% overall.")
        else:
            tips.append(f"Your portfolio is down {abs(portfolio_growth):.1f}% overall.")

    return tips
