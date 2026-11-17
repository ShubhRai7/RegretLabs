import json
import os
import time

import pandas as pd
import streamlit as st

from strategy import STRATEGIES, buy_and_hold, run_plan

st.set_page_config(page_title="Watch the robot", layout="wide")

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