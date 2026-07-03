"""
Personal Finance & Investment Tracker — Streamlit version.

Run with:  streamlit run app.py

Mock mode: auth_service, db_service, and stock_service are in-memory mocks —
no Firebase, no secrets.toml needed. See services/ for details.
"""
import streamlit as st
import pandas as pd
import calendar as cal_module
from datetime import date, datetime, timedelta

from services import auth_service, db_service, stock_service
from utils import analytics
from components import charts
import theme

st.set_page_config(page_title="Finance & Investment Tracker", page_icon="💰", layout="wide")

CURRENCY_SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}

theme.inject_css()


# ----------------------------------------------------------------------------
# Auth screens
# ----------------------------------------------------------------------------
def render_auth_screen():
    st.title("💰 Get your money into shape")
    st.caption("Track income and expenses, analyze your habits, and stick to your budgets — all in one place.")

    # While resetting a password, show ONLY the reset flow — no tabs, no
    # login/signup fields — until the user finishes or explicitly goes back.
    if st.session_state.get("show_forgot"):
        render_forgot_password_form()
        return

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        # Plain widgets (not st.form) so "Forgot password?" can sit between
        # the password field and the Log in button — st.form only allows a
        # single submit button, no other buttons inside it.
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")

        if st.button("Forgot password?", key="toggle_forgot"):
            st.session_state["show_forgot"] = True
            st.rerun()

        if st.button("Log in", key="login_submit", use_container_width=True):
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                try:
                    data = auth_service.sign_in(email, password)
                    auth_service.start_session(data)
                    st.rerun()
                except ValueError as e:
                    st.error(f"Login failed: {e}")

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Display name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (min 6 characters)", type="password", key="signup_pw")
            submitted = st.form_submit_button("Create account", use_container_width=True)
        if submitted:
            if not email or len(password) < 6:
                st.error("Enter a valid email and a password of at least 6 characters.")
            else:
                try:
                    data = auth_service.sign_up(email, password, name)
                    # sign_up only returns a session (and therefore only reaches
                    # here) when Supabase email confirmations are OFF — that's
                    # what makes this an automatic login right after signup.
                    auth_service.start_session(data)
                    st.success("Account created — you're logged in!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"Sign up failed: {e}")


def render_forgot_password_form():
    """
    Two-step reset flow using Supabase's OTP code instead of a redirect link,
    since Streamlit has no page to catch a redirect's URL token on.

    One-time setup required in the Supabase dashboard:
    Authentication -> Email Templates -> Reset Password -> remove the default
    link/button entirely and use only the code, e.g.:
        "Your password reset code is: {{ .Token }}"
    (The default template's link points at your project's Site URL, which is
    what causes a "site can't be reached" error when clicked — since this
    flow never uses that link, deleting it avoids the confusion.)
    """
    st.subheader("Reset your password")
    st.caption("We'll email you a 6-digit code to reset your password.")

    if st.button("← Back to log in", key="back_to_login"):
        st.session_state.pop("show_forgot", None)
        st.session_state.pop("reset_step", None)
        st.session_state.pop("pending_reset_email", None)
        st.rerun()

    step = st.session_state.get("reset_step", "request")

    if step == "request":
        with st.form("reset_request_form"):
            email = st.text_input("Email", key="reset_email_input")
            submitted = st.form_submit_button("Send reset code", use_container_width=True)
        if submitted:
            if not email:
                st.error("Enter your email address.")
            else:
                try:
                    auth_service.request_password_reset(email)
                    st.session_state["pending_reset_email"] = email
                    st.session_state["reset_step"] = "confirm"
                    st.rerun()
                except ValueError as e:
                    st.error(f"Could not send reset code: {e}")

    elif step == "confirm":
        st.success(f"Code sent to {st.session_state.get('pending_reset_email')}. Check your inbox.")
        with st.form("reset_confirm_form"):
            code = st.text_input("6-digit code")
            new_password = st.text_input("New password (min 6 characters)", type="password")
            submitted = st.form_submit_button("Reset password", use_container_width=True)
            back = st.form_submit_button("Use a different email", use_container_width=True)
        if back:
            st.session_state["reset_step"] = "request"
            st.rerun()
        if submitted:
            if not code or len(new_password) < 6:
                st.error("Enter the code and a password of at least 6 characters.")
            else:
                try:
                    data = auth_service.confirm_password_reset(
                        st.session_state["pending_reset_email"], code, new_password
                    )
                    auth_service.start_session(data)
                    st.session_state.pop("show_forgot", None)
                    st.session_state.pop("reset_step", None)
                    st.session_state.pop("pending_reset_email", None)
                    st.success("Password reset — you're logged in!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


# ----------------------------------------------------------------------------
# Data helpers
# ----------------------------------------------------------------------------
def compute_portfolio(uid: str) -> pd.DataFrame:
    inv_df = db_service.get_investments(uid)
    if inv_df.empty:
        return inv_df
    prices = stock_service.get_prices_bulk(inv_df["symbol"].unique().tolist())
    inv_df["currentPrice"] = inv_df["symbol"].map(lambda s: prices.get(s, {}).get("price"))
    inv_df["dayChangePct"] = inv_df["symbol"].map(lambda s: prices.get(s, {}).get("changePercent"))
    inv_df["purchaseValue"] = inv_df["purchasePrice"] * inv_df["quantity"]
    inv_df["currentValue"] = inv_df["currentPrice"] * inv_df["quantity"]
    inv_df["profitLoss"] = inv_df["currentValue"] - inv_df["purchaseValue"]
    inv_df["growthPct"] = (inv_df["profitLoss"] / inv_df["purchaseValue"]) * 100
    return inv_df


# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
def page_dashboard(uid: str, currency: str):
    st.header("📊 Dashboard")
    df = db_service.get_transactions(uid)
    portfolio_df = compute_portfolio(uid)
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    total_income = df.loc[df["type"] == "income", "amount"].sum() if not df.empty else 0
    total_expense = df.loc[df["type"] == "expense", "amount"].sum() if not df.empty else 0
    total_savings = total_income - total_expense
    portfolio_value = portfolio_df["currentValue"].sum() if not portfolio_df.empty else 0
    portfolio_growth = (
        (portfolio_df["profitLoss"].sum() / portfolio_df["purchaseValue"].sum() * 100)
        if not portfolio_df.empty and portfolio_df["purchaseValue"].sum() > 0 else 0
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Income", f"{sym}{total_income:,.0f}")
    c2.metric("Total Expenses", f"{sym}{total_expense:,.0f}")
    c3.metric("Total Savings", f"{sym}{total_savings:,.0f}")
    c4.metric("Portfolio Value", f"{sym}{portfolio_value:,.0f}")
    c5.metric("Portfolio Growth", f"{portfolio_growth:,.2f}%")

    accounts_df = db_service.get_accounts(uid)
    cards_df = db_service.get_credit_cards(uid)
    if not accounts_df.empty or not cards_df.empty:
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("🏦 Accounts")
            if accounts_df.empty:
                st.caption("No accounts added yet.")
            else:
                for _, row in accounts_df.iterrows():
                    st.write(f"{row['name']} ({row['type']}) — **{sym}{row['balance']:,.2f}**")
        with col_b:
            st.subheader("💳 Credit Cards")
            if cards_df.empty:
                st.caption("No credit cards added yet.")
            else:
                for _, row in cards_df.iterrows():
                    st.write(f"{row['name']} — due **{sym}{row['amountDue']:,.2f}** of {sym}{row['limit']:,.0f} limit")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.expense_pie_chart(analytics.category_breakdown(df))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses yet.")
    with col2:
        fig = charts.monthly_bar_chart(analytics.monthly_totals(df))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transactions yet.")

    col3, col4 = st.columns(2)
    with col3:
        fig = charts.spending_trend_line(analytics.monthly_totals(df))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending trend yet.")
    with col4:
        st.subheader("Top performing stock")
        if not portfolio_df.empty:
            top = portfolio_df.sort_values("growthPct", ascending=False).iloc[0]
            st.metric(top["symbol"], f"{sym}{top['currentValue']:,.0f}", f"{top['growthPct']:.2f}%")
        else:
            st.info("Add an investment to see top performers.")

    st.divider()
    st.subheader("Recent transactions")
    st.dataframe(
        df.head(8)[["date", "type", "category", "description", "amount"]] if not df.empty else df,
        use_container_width=True, hide_index=True,
    )

    st.subheader("Goal progress")
    goals_df = db_service.get_goals(uid)
    if goals_df.empty:
        st.info("No goals set yet — add one in the Goals tab.")
    else:
        for _, g in goals_df.iterrows():
            frac = charts.goal_progress_bar(g["currentAmount"], g["targetAmount"])
            st.write(f"**{g['title']}** — {sym}{g['currentAmount']:,.0f} / {sym}{g['targetAmount']:,.0f}")
            st.progress(frac)

    st.subheader("💡 Monthly insights")
    for tip in analytics.generate_insights(df, portfolio_growth if not portfolio_df.empty else None):
        st.write(f"- {tip}")


def page_transactions(uid: str, currency: str):
    st.header("🧾 Transactions")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    with st.expander("➕ Add a transaction", expanded=True):
        with st.form("add_tx_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            tx_type = c1.selectbox("Type", ["expense", "income"])
            category = c2.selectbox("Category", db_service.CATEGORIES)
            amount = c3.number_input("Amount", min_value=0.0, step=100.0)
            c4, c5 = st.columns(2)
            description = c4.text_input("Description")
            tx_date = c5.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Add transaction")
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                db_service.add_transaction(
                    uid, amount, category, tx_type, description, tx_date.isoformat()
                )
                st.success("Transaction added.")
                st.rerun()

    df = db_service.get_transactions(uid)
    st.subheader("Filter & search")
    c1, c2, c3 = st.columns(3)
    type_filter = c1.multiselect("Type", ["income", "expense"], default=["income", "expense"])
    cat_filter = c2.multiselect("Category", db_service.CATEGORIES, default=db_service.CATEGORIES)
    search = c3.text_input("Search description")

    filtered = df[df["type"].isin(type_filter) & df["category"].isin(cat_filter)] if not df.empty else df
    if search and not filtered.empty:
        filtered = filtered[filtered["description"].str.contains(search, case=False, na=False)]

    # Pagination
    page_size = 10
    total_rows = len(filtered)
    total_pages = max(1, (total_rows - 1) // page_size + 1)
    page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start, end = (page_num - 1) * page_size, page_num * page_size
    page_df = filtered.iloc[start:end]

    st.caption(f"Showing {min(end, total_rows)} of {total_rows} transactions")
    for _, row in page_df.iterrows():
        cols = st.columns([2, 2, 2, 3, 2, 1, 1])
        cols[0].write(row["date"])
        cols[1].write(row["type"])
        cols[2].write(row["category"])
        cols[3].write(row["description"])
        cols[4].write(f"{sym}{row['amount']:,.2f}")
        if cols[5].button("✏️", key=f"edit_{row['id']}"):
            st.session_state["editing_tx"] = row["id"]
        if cols[6].button("🗑️", key=f"del_{row['id']}"):
            db_service.delete_transaction(uid, row["id"])
            st.rerun()

    # Inline edit form
    if st.session_state.get("editing_tx"):
        tx_id = st.session_state["editing_tx"]
        tx_row = df[df["id"] == tx_id].iloc[0]
        st.subheader("Edit transaction")
        with st.form("edit_tx_form"):
            new_amount = st.number_input("Amount", value=float(tx_row["amount"]))
            new_category = st.selectbox(
                "Category", db_service.CATEGORIES,
                index=db_service.CATEGORIES.index(tx_row["category"])
                if tx_row["category"] in db_service.CATEGORIES else 0,
            )
            new_desc = st.text_input("Description", value=tx_row["description"])
            save = st.form_submit_button("Save changes")
            cancel = st.form_submit_button("Cancel")
        if save:
            db_service.update_transaction(
                uid, tx_id, amount=new_amount, category=new_category, description=new_desc
            )
            st.session_state.pop("editing_tx")
            st.rerun()
        if cancel:
            st.session_state.pop("editing_tx")
            st.rerun()


def page_investments(uid: str, currency: str):
    st.header("📈 Investments")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    with st.expander("🔍 Search a stock symbol"):
        query = st.text_input("Company name or symbol")
        if query:
            results = stock_service.search_symbol(query)
            for r in results:
                st.write(f"**{r['symbol']}** — {r['name']}")

    with st.expander("➕ Add an investment", expanded=True):
        with st.form("add_inv_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            symbol = c1.text_input("Symbol (e.g. AAPL, INFY.NS)")
            quantity = c2.number_input("Quantity", min_value=0.0, step=1.0)
            purchase_price = c3.number_input("Purchase Price", min_value=0.0, step=1.0)
            purchase_date = c4.date_input("Purchase Date", value=date.today())
            submitted = st.form_submit_button("Add investment")
        if submitted:
            if not symbol or quantity <= 0 or purchase_price <= 0:
                st.error("Enter a valid symbol, quantity, and purchase price.")
            else:
                try:
                    stock_service.get_current_price(symbol)  # validates the symbol exists
                    db_service.add_investment(
                        uid, symbol, quantity, purchase_price, purchase_date.isoformat()
                    )
                    st.success(f"Added {symbol.upper()}.")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))

    portfolio_df = compute_portfolio(uid)
    if portfolio_df.empty:
        st.info("No investments yet — add one above.")
        return

    st.subheader("Holdings")
    for _, row in portfolio_df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 2, 1])
            c1.write(f"**{row['symbol']}**")
            c2.write(f"Qty: {row['quantity']}")
            c3.write(f"Current: {sym}{row['currentPrice']:.2f}" if pd.notna(row["currentPrice"]) else "Current: N/A")
            pl_color = "🟢" if row["profitLoss"] >= 0 else "🔴"
            c4.write(f"{pl_color} P/L: {sym}{row['profitLoss']:,.2f}")
            c5.write(f"Growth: {row['growthPct']:.2f}%")
            if c6.button("🗑️", key=f"del_inv_{row['id']}"):
                db_service.delete_investment(uid, row["id"])
                st.rerun()

    st.subheader("Price history")
    chosen = st.selectbox("Symbol", portfolio_df["symbol"].unique())
    period = st.select_slider("Period", options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="6mo")
    try:
        hist = stock_service.get_historical_data(chosen, period)
        fig = charts.portfolio_growth_chart(hist, chosen)
        st.plotly_chart(fig, use_container_width=True)
    except RuntimeError as e:
        st.error(str(e))


def page_accounts(uid: str, currency: str):
    st.header("🏦 Accounts")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    df = db_service.get_accounts(uid)
    total = df["balance"].sum() if not df.empty else 0
    st.metric("Total balance", f"{sym}{total:,.2f}")

    with st.expander("➕ Add an account", expanded=df.empty):
        with st.form("add_account_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Account name")
            acc_type = c2.selectbox("Type", ["Cash", "Bank", "Wallet", "Savings"])
            balance = c3.number_input("Starting balance", step=100.0)
            submitted = st.form_submit_button("Add account")
        if submitted:
            if not name:
                st.error("Enter an account name.")
            else:
                db_service.add_account(uid, name, acc_type, balance)
                st.success("Account added.")
                st.rerun()

    if df.empty:
        st.info("No accounts yet — add one above.")
        return

    st.subheader("Your accounts")
    for _, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.write(f"**{row['name']}**")
            c2.write(row["type"])
            new_balance = c3.number_input(
                "Balance", value=float(row["balance"]), key=f"acc_bal_{row['id']}", label_visibility="collapsed"
            )
            if c3.button("Save", key=f"save_acc_{row['id']}"):
                db_service.update_account_balance(uid, row["id"], new_balance)
                st.rerun()
            if c4.button("🗑️", key=f"del_acc_{row['id']}"):
                db_service.delete_account(uid, row["id"])
                st.rerun()


def page_credit_cards(uid: str, currency: str):
    st.header("💳 Credit Cards")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    df = db_service.get_credit_cards(uid)
    total_due = df["amountDue"].sum() if not df.empty else 0
    st.metric("Total amount due", f"{sym}{total_due:,.2f}")

    with st.expander("➕ Add a credit card", expanded=df.empty):
        with st.form("add_card_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Card name")
            limit = c2.number_input("Credit limit", min_value=0.0, step=1000.0)
            amount_due = c3.number_input("Current amount due", min_value=0.0, step=100.0)
            c4, c5 = st.columns(2)
            billing_start = c4.date_input("Billing cycle start", value=date.today().replace(day=1))
            billing_end = c5.date_input("Billing cycle end", value=date.today().replace(day=1) + timedelta(days=30))
            submitted = st.form_submit_button("Add card")
        if submitted:
            if not name or limit <= 0:
                st.error("Enter a card name and a credit limit greater than 0.")
            else:
                db_service.add_credit_card(
                    uid, name, limit, amount_due, billing_start.isoformat(), billing_end.isoformat()
                )
                st.success("Card added.")
                st.rerun()

    if df.empty:
        st.info("No credit cards yet — add one above.")
        return

    st.subheader("Your cards")
    for _, row in df.iterrows():
        with st.container(border=True):
            used_pct = (row["amountDue"] / row["limit"] * 100) if row["limit"] else 0
            st.write(f"**{row['name']}** — billing {row['billingStart']} to {row['billingEnd']}")
            st.progress(min(1.0, used_pct / 100), text=f"{used_pct:.1f}% of limit used")
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"Limit: {sym}{row['limit']:,.0f}")
            c2.write(f"Due: {sym}{row['amountDue']:,.0f}")
            c3.write(f"Available: {sym}{row['limit'] - row['amountDue']:,.0f}")
            if c4.button("🗑️", key=f"del_card_{row['id']}"):
                db_service.delete_credit_card(uid, row["id"])
                st.rerun()



    st.header("🎯 Financial Goals")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    with st.expander("➕ Add a goal", expanded=True):
        with st.form("add_goal_form", clear_on_submit=True):
            title = st.text_input("Goal title (e.g. 'Save for emergency fund')")
            c1, c2 = st.columns(2)
            target = c1.number_input("Target amount", min_value=0.0, step=1000.0)
            deadline = c2.date_input("Deadline")
            submitted = st.form_submit_button("Create goal")
        if submitted:
            if not title or target <= 0:
                st.error("Enter a title and a target amount greater than 0.")
            else:
                db_service.add_goal(uid, title, target, deadline.isoformat())
                st.success("Goal created.")
                st.rerun()

    goals_df = db_service.get_goals(uid)
    if goals_df.empty:
        st.info("No goals yet — create one above.")
        return

    for _, g in goals_df.iterrows():
        with st.container(border=True):
            st.write(f"**{g['title']}** — deadline {g['deadline']}")
            frac = charts.goal_progress_bar(g["currentAmount"], g["targetAmount"])
            st.progress(frac, text=f"{sym}{g['currentAmount']:,.0f} / {sym}{g['targetAmount']:,.0f} ({frac*100:.1f}%)")
            c1, c2 = st.columns([3, 1])
            new_val = c1.number_input(
                "Update current amount", value=float(g["currentAmount"]), key=f"goal_{g['id']}"
            )
            if c1.button("Save progress", key=f"save_goal_{g['id']}"):
                db_service.update_goal_progress(uid, g["id"], new_val)
                st.rerun()
            if c2.button("Delete", key=f"del_goal_{g['id']}"):
                db_service.delete_goal(uid, g["id"])
                st.rerun()


def page_budgets(uid: str, currency: str):
    st.header("📊 Budgets")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    with st.expander("➕ Add a budget", expanded=True):
        with st.form("add_budget_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            category = c1.selectbox("Category", db_service.CATEGORIES)
            period = c2.selectbox("Period", ["weekly", "monthly"])
            limit_amount = c3.number_input("Limit amount", min_value=0.0, step=500.0)
            c4, c5 = st.columns(2)
            today = date.today()
            default_end = today + timedelta(days=6 if period == "weekly" else 29)
            start_date = c4.date_input("Start date", value=today)
            end_date = c5.date_input("End date", value=default_end)
            submitted = st.form_submit_button("Add budget")
        if submitted:
            if limit_amount <= 0:
                st.error("Enter a limit amount greater than 0.")
            else:
                db_service.add_budget(
                    uid, category, period, limit_amount, start_date.isoformat(), end_date.isoformat()
                )
                st.success("Budget added.")
                st.rerun()

    df = db_service.get_budgets(uid)
    if df.empty:
        st.info("No budgets yet — add one above.")
        return

    tab_weekly, tab_monthly = st.tabs(["Weekly budgets", "Monthly budgets"])
    for tab, period in [(tab_weekly, "weekly"), (tab_monthly, "monthly")]:
        with tab:
            subset = df[df["period"] == period]
            if subset.empty:
                st.caption(f"No {period} budgets yet.")
                continue
            for _, row in subset.iterrows():
                spent = db_service.budget_spent(uid, row["category"], row["startDate"], row["endDate"])
                frac = charts.goal_progress_bar(spent, row["limitAmount"])
                over = spent > row["limitAmount"]
                with st.container(border=True):
                    st.write(f"**{row['category']}** — {row['startDate']} to {row['endDate']}")
                    st.progress(frac, text=f"{sym}{spent:,.0f} spent of {sym}{row['limitAmount']:,.0f}")
                    if over:
                        st.warning(f"Over budget by {sym}{spent - row['limitAmount']:,.0f}")
                    else:
                        st.caption(f"{sym}{row['limitAmount'] - spent:,.0f} remaining")
                    if st.button("🗑️ Delete", key=f"del_budget_{row['id']}"):
                        db_service.delete_budget(uid, row["id"])
                        st.rerun()


def page_debts(uid: str, currency: str):
    st.header("🤝 Debts & Credits")
    st.caption("Debts = money you owe. Credits = money owed to you.")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    with st.expander("➕ Add a debt or credit", expanded=True):
        with st.form("add_debt_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            debt_type = c1.selectbox("Type", ["debt", "credit"], format_func=lambda x: "Debt (I owe)" if x == "debt" else "Credit (owed to me)")
            counterparty = c2.text_input("With whom")
            total_amount = c3.number_input("Total amount", min_value=0.0, step=500.0)
            due_date = c4.date_input("Due date", value=date.today() + timedelta(days=30))
            submitted = st.form_submit_button("Add")
        if submitted:
            if not counterparty or total_amount <= 0:
                st.error("Enter a name and an amount greater than 0.")
            else:
                db_service.add_debt(uid, debt_type, counterparty, total_amount, due_date.isoformat())
                st.success("Added.")
                st.rerun()

    df = db_service.get_debts(uid)
    if df.empty:
        st.info("No debts or credits tracked yet.")
        return

    net = (df.loc[df["type"] == "credit", "totalAmount"].sum() - df.loc[df["type"] == "credit", "paidAmount"].sum()) \
        - (df.loc[df["type"] == "debt", "totalAmount"].sum() - df.loc[df["type"] == "debt", "paidAmount"].sum())
    st.metric("Net position", f"{sym}{net:,.0f}", help="Positive means people owe you more than you owe them.")

    for _, row in df.iterrows():
        residual = row["totalAmount"] - row["paidAmount"]
        frac = charts.goal_progress_bar(row["paidAmount"], row["totalAmount"])
        label = f"{'You owe' if row['type'] == 'debt' else 'Owed to you'}: {row['counterparty']}"
        with st.container(border=True):
            st.write(f"**{label}** — due {row['dueDate']}")
            st.progress(frac, text=f"{sym}{row['paidAmount']:,.0f} paid of {sym}{row['totalAmount']:,.0f} "
                                     f"(residual {sym}{residual:,.0f})")
            c1, c2 = st.columns([3, 1])
            new_paid = c1.number_input(
                "Update paid amount", value=float(row["paidAmount"]), key=f"debt_paid_{row['id']}"
            )
            if c1.button("Save", key=f"save_debt_{row['id']}"):
                db_service.update_debt_paid(uid, row["id"], new_paid)
                st.rerun()
            if c2.button("Delete", key=f"del_debt_{row['id']}"):
                db_service.delete_debt(uid, row["id"])
                st.rerun()


def page_scheduled(uid: str, currency: str):
    st.header("🔁 Scheduled Transactions & Subscriptions")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    with st.expander("➕ Add a scheduled transaction", expanded=True):
        with st.form("add_sched_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            description = c1.text_input("Description (e.g. Netflix, Rent)")
            category = c2.selectbox("Category", db_service.CATEGORIES)
            amount = c3.number_input("Amount", min_value=0.0, step=100.0)
            c4, c5, c6 = st.columns(3)
            tx_type = c4.selectbox("Type", ["expense", "income"])
            recurrence = c5.selectbox("Repeats", ["weekly", "monthly", "yearly"])
            next_date = c6.date_input("Next date", value=date.today() + timedelta(days=7))
            is_subscription = st.checkbox("This is a subscription")
            submitted = st.form_submit_button("Add")
        if submitted:
            if not description or amount <= 0:
                st.error("Enter a description and an amount greater than 0.")
            else:
                db_service.add_scheduled(
                    uid, description, category, amount, tx_type, is_subscription, recurrence, next_date.isoformat()
                )
                st.success("Scheduled.")
                st.rerun()

    df = db_service.get_scheduled(uid)
    if df.empty:
        st.info("Nothing scheduled yet — add one above.")
        return

    subs = df[df["isSubscription"]]
    if not subs.empty:
        st.subheader("Subscriptions summary")
        monthly_equiv = {
            "weekly": lambda a: a * 52 / 12, "monthly": lambda a: a, "yearly": lambda a: a / 12,
        }
        monthly_total = sum(monthly_equiv[r["recurrence"]](r["amount"]) for _, r in subs.iterrows())
        c1, c2 = st.columns(2)
        c1.metric("Active subscriptions", len(subs))
        c2.metric("Monthly average", f"{sym}{monthly_total:,.0f}")

    st.subheader("All scheduled items")
    for _, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            tag = "📺 Subscription" if row["isSubscription"] else "🔁 Scheduled"
            c1.write(f"**{row['description']}** ({tag})")
            c2.write(f"{row['category']} · {row['recurrence']}")
            sign = "+" if row["type"] == "income" else "-"
            c3.write(f"{sign}{sym}{row['amount']:,.0f} on {row['nextDate']}")
            b1, b2 = c4.columns(2)
            if b1.button("✅ Record", key=f"record_sched_{row['id']}"):
                db_service.add_transaction(
                    uid, row["amount"], row["category"], row["type"], row["description"],
                    date.today().isoformat()
                )
                st.success(f"Recorded {row['description']} as a transaction today.")
                st.rerun()
            if b2.button("🗑️", key=f"del_sched_{row['id']}"):
                db_service.delete_scheduled(uid, row["id"])
                st.rerun()


def page_calendar(uid: str, currency: str):
    st.header("📅 Calendar")
    sym = CURRENCY_SYMBOLS.get(currency, currency)

    c1, c2 = st.columns(2)
    year = c1.selectbox("Year", list(range(date.today().year - 2, date.today().year + 2)),
                         index=2)
    month = c2.selectbox("Month", list(range(1, 13)), index=date.today().month - 1,
                          format_func=lambda m: cal_module.month_name[m])

    df = db_service.get_transactions(uid)
    daily_totals = {}
    if not df.empty:
        month_df = df[pd.to_datetime(df["date"]).dt.to_period("M") == pd.Period(year=year, month=month, freq="M")]
        for _, row in month_df.iterrows():
            d = row["date"]
            signed = row["amount"] if row["type"] == "income" else -row["amount"]
            daily_totals[d] = daily_totals.get(d, 0) + signed

    cal_module.setfirstweekday(cal_module.MONDAY)
    month_grid = cal_module.monthcalendar(year, month)

    header_cols = st.columns(7)
    for col, day_name in zip(header_cols, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        col.markdown(f"**{day_name}**")

    for week in month_grid:
        week_cols = st.columns(7)
        for col, day in zip(week_cols, week):
            if day == 0:
                col.write("")
                continue
            d_str = date(year, month, day).isoformat()
            net = daily_totals.get(d_str)
            with col.container(border=True):
                st.write(f"**{day}**")
                if net is not None:
                    color = theme.PRIMARY if net >= 0 else "#FF6584"
                    st.markdown(f"<span style='color:{color};font-weight:600'>{sym}{net:,.0f}</span>",
                                unsafe_allow_html=True)



    st.header("⚙️ Settings")
    st.subheader("Personalization")
    dark_mode = st.toggle("Dark mode (visual preference, saved to your profile)", value=prefs.get("darkMode", False))
    currency = st.selectbox(
        "Currency", list(CURRENCY_SYMBOLS.keys()),
        index=list(CURRENCY_SYMBOLS.keys()).index(prefs.get("currency", "INR")),
    )
    if st.button("Save preferences"):
        db_service.update_preferences(uid, darkMode=dark_mode, currency=currency,
                                       widgetOrder=prefs.get("widgetOrder", []))
        st.success("Preferences saved.")
        st.rerun()

    if dark_mode:
        st.markdown(
            "<style>.stApp{background-color:#0e1117;color:#fafafa;}</style>",
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------------
# Main router
# ----------------------------------------------------------------------------
def main():
    if not auth_service.is_authenticated():
        render_auth_screen()
        return

    user = auth_service.current_user()
    uid = user["uid"]
    prefs = db_service.get_preferences(uid) or {}
    currency = prefs.get("currency", "INR")

    if prefs.get("darkMode"):
        st.markdown("<style>.stApp{background-color:#0e1117;color:#fafafa;}</style>", unsafe_allow_html=True)

    with st.sidebar:
        st.title("💰 Spendee-style Tracker")
        st.caption(f"Logged in as {user['email']}")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        page = theme.render_sidebar_nav()
        st.divider()
        if st.button("Log out", use_container_width=True):
            auth_service.logout()
            st.rerun()

    try:
        if page == "Dashboard":
            page_dashboard(uid, currency)
        elif page == "Transactions":
            page_transactions(uid, currency)
        elif page == "Scheduled":
            page_scheduled(uid, currency)
        elif page == "Accounts":
            page_accounts(uid, currency)
        elif page == "Credit Cards":
            page_credit_cards(uid, currency)
        elif page == "Budgets":
            page_budgets(uid, currency)
        elif page == "Debts":
            page_debts(uid, currency)
        elif page == "Investments":
            page_investments(uid, currency)
        elif page == "Goals":
            page_goals(uid, currency)
        elif page == "Calendar":
            page_calendar(uid, currency)
        elif page == "Settings":
            page_settings(uid, prefs)
    except Exception as e:
        st.error(f"Something went wrong: {e}")


if __name__ == "__main__":
    main()
