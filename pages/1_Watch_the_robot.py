import json
import os
import time

import pandas as pd
import streamlit as st

from strategy import STRATEGIES, buy_and_hold, run_plan

st.set_page_config(page_title="Watch the robot", layout="wide")

# ===== REGRET REPLAY — MIDNIGHT LEDGER THEME =====

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --rr-bg: #080d16;
    --rr-panel: #101925;
    --rr-panel-2: #152231;
    --rr-border: rgba(160,180,205,.13);
    --rr-border-strong: rgba(160,180,205,.26);
    --rr-text: #edf2f7;
    --rr-muted: #8d9bad;
    --rr-green: #3fd49b;
    --rr-green-deep: #25a577;
    --rr-glow: rgba(63,212,155,.30);
    --rr-amber: #e5b76a;
}

/* ---------- page ---------- */
.stApp {
    background:
        radial-gradient(ellipse at 12% 0%, rgba(42,92,87,.18), transparent 34%),
        radial-gradient(ellipse at 92% 10%, rgba(57,76,112,.14), transparent 30%),
        var(--rr-bg);
    color: var(--rr-text);
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: rgba(8,13,22,.72); }
.block-container { max-width: 1440px; padding-top: 2.1rem; padding-bottom: 4rem; }
::selection { background: rgba(63,212,155,.28); }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #1f2d40; border-radius: 8px; border: 2px solid var(--rr-bg); }
::-webkit-scrollbar-thumb:hover { background: #2c4160; }
hr { border-color: var(--rr-border) !important; }

/* ---------- type ---------- */
h1, h2, h3, h4 {
    font-family: 'Manrope', sans-serif !important;
    letter-spacing: -.035em;
    color: var(--rr-text) !important;
}
h1 { font-size: clamp(2.1rem,4vw,3.25rem) !important; font-weight: 800 !important; }
[data-testid="stCaptionContainer"] { color: var(--rr-muted) !important; }
[data-testid="stWidgetLabel"] p, label {
    color: var(--rr-muted) !important;
    font-weight: 600;
    font-size: .82rem;
    letter-spacing: .02em;
}

/* ---------- metric cards ---------- */
[data-testid="stMetric"] {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg,#152231,#0e1824);
    border: 1px solid var(--rr-border);
    border-radius: 14px;
    padding: 17px 18px;
    box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 28px rgba(0,0,0,.28);
    transition: border-color .2s, box-shadow .2s;
}
[data-testid="stMetric"]::before {
    content: "";
    position: absolute; left: 0; top: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--rr-green), transparent 70%);
}
[data-testid="stMetric"]:hover {
    border-color: rgba(63,212,155,.40);
    box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 28px rgba(0,0,0,.28), 0 0 26px rgba(63,212,155,.12);
}
[data-testid="stMetricLabel"] {
    color: var(--rr-muted) !important;
    text-transform: uppercase;
    letter-spacing: .08em;
}
[data-testid="stMetricValue"] {
    color: var(--rr-text) !important;
    font-family: 'Manrope', sans-serif;
    font-weight: 750;
    font-variant-numeric: tabular-nums;
}

/* ---------- buttons ---------- */
.stButton > button {
    background: #172536;
    color: #eaf2f7;
    border: 1px solid var(--rr-border);
    border-radius: 10px;
    min-height: 2.65rem;
    font-weight: 650;
    transition: border-color .15s, box-shadow .15s, background .15s;
}
.stButton > button:hover {
    border-color: var(--rr-green);
    color: #a5ebce;
    background: #1b3040;
    box-shadow: 0 0 18px rgba(63,212,155,.16);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#43d9a0,#25a577);
    color: #05140d;
    border: 0;
    box-shadow: 0 6px 22px rgba(63,212,155,.24);
}
.stButton > button[kind="primary"]:hover {
    color: #05140d;
    box-shadow: 0 8px 30px rgba(63,212,155,.42);
}
.stButton > button:disabled { opacity: .45; }

/* ---------- inputs, dropdowns (closed and open) ---------- */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background: #111e2c !important;
    border-color: var(--rr-border) !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"]:focus-within > div,
div[data-baseweb="input"]:focus-within > div {
    border-color: var(--rr-green) !important;
    box-shadow: 0 0 0 3px rgba(63,212,155,.16) !important;
}
/* newer Streamlit (React Aria widgets) */
.react-aria-ComboBox > [role="group"] {
    background: #111e2c !important;
    border-color: var(--rr-border) !important;
    border-radius: 10px !important;
}
.react-aria-ComboBox[data-open="true"] > [role="group"],
.react-aria-ComboBox > [role="group"][data-focus-within="true"] {
    border-color: var(--rr-green) !important;
    box-shadow: 0 0 0 3px rgba(63,212,155,.16) !important;
}
[data-testid="stSelectboxVirtualDropdown"] {
    background: var(--rr-panel) !important;
    border: 1px solid var(--rr-border-strong);
    border-radius: 12px;
    box-shadow: 0 18px 48px rgba(0,0,0,.6), 0 0 0 1px rgba(63,212,155,.07);
}
div[role="option"]:hover,
div[role="option"][data-focused="true"] { background: rgba(63,212,155,.10) !important; }
div[role="option"][data-selected="true"] {
    background: rgba(63,212,155,.16) !important;
    color: #c9f7e3 !important;
}
span[data-tag] {
    background: rgba(63,212,155,.14) !important;
    border: 1px solid rgba(63,212,155,.38);
    border-radius: 8px !important;
    color: #c9f7e3 !important;
}

/* older Streamlit (BaseUI widgets) */
div[data-baseweb="popover"] > div {
    background: var(--rr-panel) !important;
    border: 1px solid var(--rr-border-strong);
    border-radius: 12px;
    box-shadow: 0 18px 48px rgba(0,0,0,.6), 0 0 0 1px rgba(63,212,155,.07);
}
div[data-baseweb="menu"], ul[role="listbox"] { background: var(--rr-panel) !important; }
li[role="option"] { background: transparent !important; color: var(--rr-text) !important; }
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background: rgba(63,212,155,.13) !important;
    color: #c9f7e3 !important;
}
span[data-baseweb="tag"] {
    background: rgba(63,212,155,.14) !important;
    border: 1px solid rgba(63,212,155,.35);
    border-radius: 8px !important;
    color: #c9f7e3 !important;
}
[data-testid="stNumberInput"] button {
    background: var(--rr-panel-2) !important;
    border-color: var(--rr-border) !important;
    color: var(--rr-text) !important;
}
[data-testid="stNumberInput"] button:hover { color: var(--rr-green) !important; }

/* ---------- slider ---------- */
[data-testid="stSlider"] [role="slider"] {
    background: var(--rr-green) !important;
    box-shadow: 0 0 0 4px rgba(63,212,155,.18), 0 0 14px var(--rr-glow);
}
[data-testid="stSliderThumbValue"] {
    color: var(--rr-green) !important;
    font-family: 'DM Mono', monospace;
}

/* ---------- tabs ---------- */
button[data-baseweb="tab"] { color: var(--rr-muted); font-weight: 600; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--rr-green); }
div[data-baseweb="tab-highlight"] { background: var(--rr-green) !important; box-shadow: 0 0 12px var(--rr-glow); }
div[data-baseweb="tab-border"] { background: var(--rr-border) !important; }

/* ---------- expanders, alerts ---------- */
div[data-testid="stExpander"] {
    border-color: var(--rr-border) !important;
    border-radius: 14px !important;
    background: rgba(16,25,37,.72);
}
[data-testid="stExpander"] summary:hover { color: var(--rr-green); }
[data-testid="stAlert"],
[data-testid="stAlertContainer"] { border-radius: 12px; border: 1px solid var(--rr-border); }

/* ---------- tables ---------- */
[data-testid="stDataFrame"] {
    border: 1px solid var(--rr-border);
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stTable"] table {
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid var(--rr-border);
    border-radius: 12px;
    overflow: hidden;
    background: var(--rr-panel);
}
[data-testid="stTable"] th {
    background: var(--rr-panel-2) !important;
    color: var(--rr-muted) !important;
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .08em;
    border-bottom: 1px solid var(--rr-border-strong) !important;
}
[data-testid="stTable"] td {
    color: var(--rr-text);
    font-size: .9rem;
    vertical-align: top;
    border-color: var(--rr-border) !important;
}

/* ---------- sidebar / navigation ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0b1220,#080d16);
    border-right: 1px solid var(--rr-border);
}
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNavLink"] {
    border-radius: 10px;
    transition: background .15s;
}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNavLink"]:hover { background: rgba(63,212,155,.09); }
[data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(63,212,155,.13);
    box-shadow: inset 3px 0 0 var(--rr-green);
}

@media (max-width: 700px) {
    .block-container { padding: 1.2rem 1rem 3rem; }
}
</style>
""", unsafe_allow_html=True)
# ===== REGRETLABS BRANDING =====

st.markdown("""
<div style="
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:14px 18px;
    margin-bottom:24px;
    border:1px solid rgba(160,180,205,.13);
    border-radius:14px;
    background:linear-gradient(110deg,#142130,#0d1622);
">
    <div style="display:flex;align-items:center;gap:12px;">
        <div style="
            width:34px;height:34px;
            border-radius:10px;
            display:grid;place-items:center;
            background:#55c59a;
            color:#07140f;
            font-weight:800;
        ">R</div>
        <div>
            <div style="font-weight:800;color:#f2f6fa;">
                REGRET REPLAY
            </div>
            <div style="
                color:#91a1b4;
                font-size:10px;
                letter-spacing:2px;
            ">BY SHREEMANT</div>
        </div>
    </div>
    <div style="
        color:#9eacbd;
        font-size:10px;
        letter-spacing:1px;
    ">THE MIDNIGHT LEDGER</div>
</div>
""", unsafe_allow_html=True)


START_CASH = 100000


# ---------- LOADING DATA ----------
@st.cache_data
def load_prices(file_name):
    return pd.read_csv(f"data/{file_name}")


def load_periods():
    try:
        with open("data/periods.json") as f:
            found = json.load(f)["periods"]
        found = [p for p in found if os.path.exists(f"data/{p['prices_file']}")]
        if found:
            return found
    except Exception:
        pass
    return [
        {
            "number": 1,
            "prices_file": "prices_period1.csv",
            "key_file": "answer_key.json",
            "days": None,
        }
    ]


# ---------- TITLE ----------
st.title("Watch the robot")
st.caption(
    "No game and no trades from you. Pick a scenario and one or more plans, "
    "then watch how each plan trades on its own with pretend money."
)

# ---------- CHOICES ----------
periods = load_periods()
by_number = {p["number"]: p for p in periods}
plan_ids = list(STRATEGIES.keys())

c1, c2 = st.columns([1, 2])
c1.selectbox(
    "Scenario",
    list(by_number.keys()),
    format_func=lambda n: f"Scenario {n}"
    + (f"  ({by_number[n]['days']} trading days)" if by_number[n]["days"] else ""),
    key="robot_period",
)
chosen = c2.multiselect(
    "Plans to watch (pick one or several)",
    plan_ids,
    default=plan_ids,
    format_func=lambda p: STRATEGIES[p]["name"],
    key="robot_plans",
)

if not chosen:
    st.info("Pick at least one plan to watch.")
    st.stop()

period = by_number[st.session_state.robot_period]
prices = load_prices(period["prices_file"])
stocks = [c for c in prices.columns if c != "Day"]
total_days = len(prices)

# Every chosen plan trades on its own over the same prices
results = {}
for pid in chosen:
    results[pid] = run_plan(pid, prices, stocks, START_CASH)
hold = buy_and_hold(prices, stocks, START_CASH)

with st.expander("What each plan does"):
    st.table(
        pd.DataFrame(
            [
                {
                    "Plan": STRATEGIES[p]["name"],
                    "Buys when": STRATEGIES[p]["buy_when"],
                    "Sells when": STRATEGIES[p]["sell_when"],
                }
                for p in chosen
            ]
        ).set_index("Plan")
    )


# ---------- DRAWING THE REPLAY ----------
def scoreboard(day):
    rows = []
    for pid in chosen:
        values, signals = results[pid]
        upto = values.iloc[:day]
        rows.append(
            {
                "Plan": STRATEGIES[pid]["name"],
                "_value": float(upto.iloc[-1]),
                "Trades so far": sum(1 for s in signals if s["day"] <= day),
                "Biggest drop (%)": round(float((upto / upto.cummax() - 1).min() * 100), 1),
            }
        )
    hold_upto = hold.iloc[:day]
    hold_value = float(hold_upto.iloc[-1])
    rows.append(
        {
            "Plan": "Buy and hold (baseline)",
            "_value": hold_value,
            "Trades so far": 0,
            "Biggest drop (%)": round(float((hold_upto / hold_upto.cummax() - 1).min() * 100), 1),
        }
    )
    rows.sort(key=lambda r: r["_value"], reverse=True)
    table = []
    for r in rows:
        table.append(
            {
                "Plan": r["Plan"],
                "Value (₹)": f"₹{r['_value']:,.0f}",
                "Gain or loss": f"{(r['_value'] / START_CASH - 1) * 100:+.1f}%",
                "Versus buy and hold": f"₹{r['_value'] - hold_value:+,.0f}",
                "Trades so far": r["Trades so far"],
                "Biggest drop (%)": r["Biggest drop (%)"],
            }
        )
    return pd.DataFrame(table), rows


def draw(day, chart_slot, board_slot, note_slot):
    data = {
        STRATEGIES[pid]["name"]: results[pid][0].iloc[:day].values for pid in chosen
    }
    data["Buy and hold"] = hold.iloc[:day].values
    chart_slot.line_chart(pd.DataFrame(data, index=prices["Day"].iloc[:day]))

    table, rows = scoreboard(day)
    board_slot.dataframe(table, hide_index=True, width="stretch")

    plan_rows = [r for r in rows if r["Plan"] != "Buy and hold (baseline)"]
    hold_row = next(r for r in rows if r["Plan"] == "Buy and hold (baseline)")
    best, worst = plan_rows[0], plan_rows[-1]
    beat = [r["Plan"] for r in plan_rows if r["_value"] > hold_row["_value"]]
    text = (
        f"By Day {day}: best plan is **{best['Plan']}** "
        f"({(best['_value'] / START_CASH - 1) * 100:+.1f}%), weakest is **{worst['Plan']}** "
        f"({(worst['_value'] / START_CASH - 1) * 100:+.1f}%), and buy and hold is at "
        f"{(hold_row['_value'] / START_CASH - 1) * 100:+.1f}%. "
    )
    if beat:
        text += f"Plans ahead of buy and hold: {', '.join(beat)}."
    else:
        text += "No plan has beaten simply buying and holding so far."
    note_slot.markdown(text)


# ---------- THE REPLAY ----------
st.subheader("The replay")
day = st.slider("Show the replay up to day", 1, total_days, total_days, key="robot_day")
play = st.button("▶ Play from Day 1")

chart_slot = st.empty()
note_slot = st.empty()
st.subheader("Scoreboard")
board_slot = st.empty()

if play:
    step = max(1, total_days // 60)
    for d in list(range(1, total_days + 1, step)) + [total_days]:
        draw(d, chart_slot, board_slot, note_slot)
        time.sleep(0.05)
else:
    draw(day, chart_slot, board_slot, note_slot)

# ---------- EVERY BUY AND SELL ----------
with st.expander("See every buy and sell the robot made"):
    log = []
    for pid in chosen:
        for s in results[pid][1]:
            if s["day"] <= day:
                log.append(
                    {
                        "Plan": STRATEGIES[pid]["name"],
                        "Day": s["day"],
                        "Stock": s["stock"],
                        "Action": s["action"],
                        "Price": round(float(prices.loc[s["day"] - 1, s["stock"]]), 2),
                    }
                )
    if log:
        st.dataframe(
            pd.DataFrame(log).sort_values(["Day", "Plan"]), hide_index=True
        )
    else:
        st.write("No trades yet by this day.")

# ---------- SPOILER ----------
with st.expander("Reveal what this scenario was (spoiler)"):
    with open(f"data/{period['key_file']}") as f:
        key_data = json.load(f)
    st.write(
        f"Scenario {period['number']} was **{key_data['dates'][0]}** to "
        f"**{key_data['dates'][-1]}**."
    )
    if key_data.get("story"):
        st.write(key_data["story"])
    for name, ticker in key_data["companies"].items():
        st.write(f"- {name} was **{ticker.replace('.NS', '')}**")