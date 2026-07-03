"""Plotly chart builders used by the Streamlit pages — Spendee-style palette."""
import plotly.express as px
import plotly.graph_objects as go

import theme

FONT = dict(family="Inter, sans-serif", color=theme.TEXT_DARK)


def _base_layout(fig):
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        font=FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=FONT),
    )
    return fig


def expense_pie_chart(df):
    if df is None or df.empty:
        return None
    fig = px.pie(df, names="category", values="amount", hole=0.55,
                 color_discrete_sequence=theme.CHART_COLORS)
    fig.update_traces(textfont=FONT)
    return _base_layout(fig)


def monthly_bar_chart(df):
    if df is None or df.empty:
        return None
    fig = px.bar(df, x="month", y="amount", color="type", barmode="group",
                 color_discrete_map={"income": theme.PRIMARY, "expense": theme.CHART_COLORS[2]})
    return _base_layout(fig)


def spending_trend_line(df):
    if df is None or df.empty:
        return None
    expense_df = df[df["type"] == "expense"]
    if expense_df.empty:
        return None
    fig = px.line(expense_df, x="month", y="amount", markers=True,
                  color_discrete_sequence=[theme.PRIMARY])
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    return _base_layout(fig)


def portfolio_growth_chart(hist_df, symbol: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_df["date"], y=hist_df["close"], mode="lines", name=symbol,
        line=dict(color=theme.PRIMARY, width=3),
        fill="tozeroy", fillcolor="rgba(0, 196, 140, 0.08)",
    ))
    fig.update_layout(yaxis_title="Price")
    return _base_layout(fig)


def goal_progress_bar(current, target) -> float:
    if not target:
        return 0.0
    return max(0.0, min(1.0, current / target))
