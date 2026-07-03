"""
Spendee-inspired visual theme.

Reference: https://www.spendee.com — clean white canvas, a single confident
mint-green accent, soft rounded cards with light shadows, a friendly
geometric sans-serif (Poppins for headings, Inter for body text), and a
simple icon-led sidebar nav with a green highlight on the active page.

Change the values below to re-theme the whole app from one place.
"""
import streamlit as st

# ---- Palette -----------------------------------------------------------
PRIMARY = "#00C48C"        # Spendee's signature mint green
PRIMARY_DARK = "#00A876"   # hover / pressed state
PRIMARY_SOFT = "#E6FAF3"   # tint used for selected nav pill / soft badges

BG = "#F6F8FB"             # page background — soft off-white, not stark white
CARD_BG = "#FFFFFF"
TEXT_DARK = "#1F2A37"
TEXT_MUTED = "#6B7280"
BORDER = "#EDF1F5"

# A friendly, varied palette for charts (category pies, bars) —
# mirrors Spendee's colorful-but-clean category color coding.
CHART_COLORS = ["#00C48C", "#7B61FF", "#FF6584", "#FFC542", "#4D96FF", "#2EC4B6", "#FF9F5A"]

NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Transactions", "🧾"),
    ("Scheduled", "🔁"),
    ("Accounts", "🏦"),
    ("Credit Cards", "💳"),
    ("Budgets", "📊"),
    ("Debts", "🤝"),
    ("Investments", "📈"),
    ("Goals", "🎯"),
    ("Calendar", "📅"),
    ("Settings", "⚙️"),
]


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {TEXT_DARK};
        }}
        h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 600 !important;
            color: {TEXT_DARK} !important;
        }}

        /* Page background */
        .stApp {{
            background-color: {BG};
        }}

        /* ---- Sidebar: white card, icon-led nav with green highlight ---- */
        section[data-testid="stSidebar"] {{
            background-color: {CARD_BG};
            border-right: 1px solid {BORDER};
        }}
        section[data-testid="stSidebar"] h1 {{
            font-size: 1.3rem !important;
            color: {PRIMARY_DARK} !important;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] {{
            gap: 4px;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            background-color: transparent;
            border-radius: 10px;
            padding: 10px 14px !important;
            margin-bottom: 2px;
            transition: background-color 0.15s ease;
            width: 100%;
            display: flex !important;
            align-items: center;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background-color: {PRIMARY_SOFT};
        }}
        /* Always keep the icon+text visible, regardless of its position in the DOM */
        section[data-testid="stSidebar"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }}
        /* Hide only the wrapper that does NOT contain the text (i.e. the native radio circle) */
        section[data-testid="stSidebar"] div[role="radiogroup"] label > div:not(:has([data-testid="stMarkdownContainer"])) {{
            display: none;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background-color: {PRIMARY_SOFT};
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
            color: {PRIMARY_DARK} !important;
            font-weight: 600 !important;
        }}

        /* ---- Buttons: pill-shaped, mint green ---- */
        div.stButton > button,
        div.stFormSubmitButton > button,
        div.stDownloadButton > button {{
            background-color: {PRIMARY} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 0.5rem 1.3rem !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 6px rgba(0, 196, 140, 0.25);
        }}
        div.stButton > button:hover,
        div.stFormSubmitButton > button:hover,
        div.stDownloadButton > button:hover {{
            background-color: {PRIMARY_DARK} !important;
            box-shadow: 0 4px 10px rgba(0, 196, 140, 0.35);
        }}
        div.stButton > button p,
        div.stFormSubmitButton > button p {{
            color: #ffffff !important;
        }}

        /* ---- Cards: containers, metrics, expanders, forms ---- */
        div[data-testid="stMetric"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 2px 8px rgba(31, 42, 55, 0.04);
        }}
        div[data-testid="stMetricLabel"] {{
            color: {TEXT_MUTED} !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: {TEXT_DARK} !important;
            font-family: 'Poppins', sans-serif !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            border: 1px solid {BORDER} !important;
            background-color: {CARD_BG} !important;
        }}
        div[data-testid="stExpander"] {{
            border-radius: 14px !important;
            border: 1px solid {BORDER} !important;
            background-color: {CARD_BG} !important;
            overflow: hidden;
        }}
        div[data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
        }}

        /* Progress bars in the brand green */
        div[data-testid="stProgress"] > div > div {{
            background-color: {PRIMARY} !important;
        }}

        /* Tabs underline in brand green */
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {PRIMARY_DARK} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {PRIMARY} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_nav() -> str:
    """Icon-led nav radio, styled as pills via inject_css(). Returns the selected page name."""
    labels = [f"{icon}  {name}" for name, icon in NAV_ITEMS]
    choice = st.radio("Navigate", labels, label_visibility="collapsed")
    return choice.split("  ", 1)[1]  # strip the icon back off
