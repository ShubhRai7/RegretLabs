import json
import os

import pandas as pd
import streamlit as st

from ai import get_coaching
from rules import RULES, replay_with_rules
from strategy import (
    STRATEGIES,
    buy_and_hold,
    check_trades,
    missed_signals,
    player_values,
    run_plan,
)

st.set_page_config(page_title="Regret Replay", layout="wide")

START_CASH = 100000
STOCK_NAMES = ["Stock A", "Stock B", "Stock C", "Stock D", "Stock E"]


# ---------- LOADING DATA ----------
@st.cache_data
def load_prices(file_name):
    return pd.read_csv(f"data/{file_name}")


def load_periods():
    """The list of scenarios. Falls back to a single scenario if get_data.py was not re-run."""
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


# ---------- GAME FUNCTIONS ----------
def reset_game():
    st.session_state.day = 0
    st.session_state.cash = START_CASH
    st.session_state.shares = {s: 0 for s in STOCK_NAMES}
    st.session_state.trades = []
    st.session_state.msg = ""
    st.session_state.pop("coach", None)


def price_today(stock):
    return float(prices.loc[st.session_state.day, stock])


def holdings_value():
    return sum(st.session_state.shares[s] * price_today(s) for s in stocks)


def next_day():
    if st.session_state.day < len(prices) - 1:
        st.session_state.day += 1
        st.session_state.msg = ""


def skip_ten():
    st.session_state.day = min(st.session_state.day + 10, len(prices) - 1)
    st.session_state.msg = ""


def trade(action):
    stock = st.session_state.sel_stock
    qty = int(st.session_state.qty)
    price = price_today(stock)
    cost = price * qty

    if action == "BUY":
        if cost > st.session_state.cash:
            st.session_state.msg = "Not enough cash for that."
            return
        st.session_state.cash -= cost
        st.session_state.shares[stock] += qty
    else:
        if qty > st.session_state.shares[stock]:
            st.session_state.msg = "You don't own that many shares."
            return
        st.session_state.cash += cost
        st.session_state.shares[stock] -= qty

    st.session_state.trades.append(
        {
            "day": int(prices.loc[st.session_state.day, "Day"]),
            "stock": stock,
            "action": action,
            "quantity": qty,
            "price": round(price, 2),
            "total": round(cost, 2),
        }
    )
    st.session_state.msg = (
        f"Done: {action} {qty} of {stock} at ₹{price:,.2f} each. Total: ₹{cost:,.2f}"
    )


# Set up a fresh game the first time the page loads
if "day" not in st.session_state:
    reset_game()

# ---------- TITLE ----------
st.title("Regret Replay")
st.caption("Pretend money. Real market history, with names and dates hidden.")

locked = st.session_state.day > 0 or len(st.session_state.trades) > 0

# ---------- STEP 1: CHOOSE YOUR SCENARIO ----------
periods = load_periods()
by_number = {p["number"]: p for p in periods}

st.subheader("Step 1: Choose a scenario")
st.selectbox(
    "Scenario (each one is a different stretch of real market history)",
    list(by_number.keys()),
    format_func=lambda n: f"Scenario {n}"
    + (f"  ({by_number[n]['days']} trading days)" if by_number[n]["days"] else ""),
    key="period_no",
    disabled=locked,
)
period = by_number[st.session_state.period_no]
st.caption(
    "You won't be told which years or which companies. That is revealed at the end."
)
if len(periods) == 1:
    st.info(
        "Only 1 scenario found. Run `python get_data.py` in the terminal to create the other 4."
    )

prices = load_prices(period["prices_file"])
stocks = [c for c in prices.columns if c != "Day"]

# ---------- STEP 2: CHOOSE YOUR PLAN ----------
plan_ids = list(STRATEGIES.keys())

st.subheader("Step 2: Choose your plan")
st.selectbox(
    "Your plan (open the list to see all 5)",
    plan_ids,
    format_func=lambda p: f"{STRATEGIES[p]['name']}  —  {STRATEGIES[p]['tagline']}",
    key="plan_id",
    disabled=locked,
)
plan_id = st.session_state.plan_id
plan_info = STRATEGIES[plan_id]

with st.container(border=True):
    st.markdown(f"### {plan_info['name']}")
    st.write(plan_info["tagline"])
    st.markdown(
        f"**Buys when:** {plan_info['buy_when']}\n\n"
        f"**Sells when:** {plan_info['sell_when']}\n\n"
        f"**How the money is used:** {plan_info['money']}\n\n"
        f"**Personality:** {plan_info['style']}\n\n"
        f"**Works best when:** {plan_info['best_when']}\n\n"
        f"**Struggles when:** {plan_info['struggles_when']}"
    )

with st.expander("Compare all 5 plans side by side"):
    rows = []
    for pid in plan_ids:
        info = STRATEGIES[pid]
        rows.append(
            {
                "Plan": info["name"],
                "Buys when": info["buy_when"],
                "Sells when": info["sell_when"],
                "Personality": info["style"],
                "Works best when": info["best_when"],
                "Struggles when": info["struggles_when"],
            }
        )
    st.table(pd.DataFrame(rows).set_index("Plan"))

if locked:
    st.caption(
        "Your scenario and plan are locked once the game starts, so you can't change "
        "your mind halfway. Press 'Restart game' further down to pick again."
    )

# The plan trades on its own over the same prices (used for all comparisons)
plan_values, plan_signals = run_plan(plan_id, prices, stocks, START_CASH)

# ---------- TOP OF THE PAGE ----------
day_number = int(prices.loc[st.session_state.day, "Day"])
total = st.session_state.cash + holdings_value()

st.subheader("Step 3: Play")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Day", f"{day_number} of {len(prices)}")
m2.metric("Cash", f"₹{st.session_state.cash:,.0f}")
m3.metric("Shares worth", f"₹{holdings_value():,.0f}")
m4.metric("Total value", f"₹{total:,.0f}")

st.subheader("Prices so far")
st.line_chart(prices.set_index("Day").iloc[: st.session_state.day + 1])

# ---------- WHAT THE PLAN SAYS TODAY ----------
st.subheader("What your plan says today")
today_signals = [s for s in plan_signals if s["day"] == day_number]
if today_signals:
    lines = ", ".join(f"{s['action']} {s['stock']}" for s in today_signals)
    st.success(f"**{plan_info['name']}** says: **{lines}**")
else:
    st.info(f"**{plan_info['name']}** says: **do nothing today (hold).**")
st.caption(
    "You don't have to obey it. But every time you do something different, "
    "the app counts it as going off plan."
)

# ---------- YOUR MOVE ----------
st.subheader("Your move")
col_stock, col_qty, col_buy, col_sell = st.columns([2, 1, 1, 1])
col_stock.selectbox("Stock", stocks, key="sel_stock")
col_qty.number_input("How many shares", min_value=1, value=100, step=1, key="qty")
col_buy.button("Buy", on_click=trade, args=("BUY",), use_container_width=True)
col_sell.button("Sell", on_click=trade, args=("SELL",), use_container_width=True)

sel = st.session_state.sel_stock
qty_now = int(st.session_state.qty)
unit_price = price_today(sel)
order_total = unit_price * qty_now
st.write(
    f"**Order total:** ₹{unit_price:,.2f} × {qty_now} shares = **₹{order_total:,.2f}**"
)
st.caption(
    f"You have ₹{st.session_state.cash:,.0f} cash and own "
    f"{st.session_state.shares[sel]} shares of {sel}."
)
if order_total > st.session_state.cash:
    st.warning("This order is bigger than your cash, so a Buy would be blocked.")

if st.session_state.msg:
    st.info(st.session_state.msg)

col_next, col_skip, col_restart = st.columns([1, 2, 1])
col_next.button("Next Day ➜", on_click=next_day, type="primary")
col_skip.button("Fast-forward 10 days (for testing)", on_click=skip_ten)
col_restart.button("Restart game", on_click=reset_game)

if st.session_state.day == len(prices) - 1:
    st.success("The period is over. Final value: ₹{:,.0f}".format(total))

# ---------- WHAT YOU OWN, TRADE RECORD ----------
st.subheader("What you own today")
owned = pd.DataFrame(
    {
        "Stock": stocks,
        "Shares": [st.session_state.shares[s] for s in stocks],
        "Price today": [round(price_today(s), 2) for s in stocks],
    }
)
st.dataframe(owned, hide_index=True)

st.subheader("Your trade record")
if st.session_state.trades:
    st.dataframe(pd.DataFrame(st.session_state.trades), hide_index=True)
else:
    st.write("No trades yet.")

# ---------- RESULTS: YOU vs THE PLAN vs BUY AND HOLD ----------
st.divider()
st.header("Results so far")

last = st.session_state.day
mine = player_values(prices, stocks, st.session_state.trades, START_CASH, last)
hold = buy_and_hold(prices, stocks, START_CASH).iloc[: last + 1]
plan = plan_values.iloc[: last + 1]

chart = pd.DataFrame(
    {
        "You": mine.values,
        f"Plan on autopilot ({plan_info['name']})": plan.values,
        "Buy and hold": hold.values,
    },
    index=prices["Day"].iloc[: last + 1],
)
st.line_chart(chart)

r1, r2, r3 = st.columns(3)
r1.metric("You", f"₹{mine.iloc[-1]:,.0f}")
r2.metric("Plan on autopilot", f"₹{plan.iloc[-1]:,.0f}")
r3.metric("Buy and hold", f"₹{hold.iloc[-1]:,.0f}")

gap = plan.iloc[-1] - mine.iloc[-1]
st.write(f"Plan minus you: **₹{gap:,.0f}**")

# ---------- DID YOU FOLLOW THE PLAN? ----------
st.divider()
st.header("Did you follow the plan?")

with st.expander("See everything the plan did on autopilot"):
    shown = [s for s in plan_signals if s["day"] - 1 <= last]
    if shown:
        st.dataframe(pd.DataFrame(shown), hide_index=True)
    else:
        st.write("The plan hasn't traded yet.")

if not st.session_state.trades:
    st.write("Make some trades first, then come back here.")
else:
    checked = check_trades(prices, st.session_state.trades, plan_signals, last)
    off = checked[checked["Followed plan?"] != "Yes"]
    score = (len(checked) - len(off)) / len(checked) * 100

    f1, f2, f3 = st.columns(3)
    f1.metric("Discipline score", f"{score:.0f}%")
    f2.metric("Off-plan trades", f"{len(off)} of {len(checked)}")
    f3.metric(
        "Result of off-plan trades",
        f"₹{off['Result after 10 days (Rs)'].sum():,.0f}",
    )
    st.dataframe(checked, hide_index=True)

    st.subheader("Moments the plan acted but you did nothing")
    missed = missed_signals(st.session_state.trades, plan_signals, last)
    if len(missed) == 0:
        st.write("None so far.")
    else:
        st.dataframe(missed, hide_index=True)

# ---------- AI COACH AND BETTER-HABITS RULES ----------
st.divider()
st.header("Your coaching report")

has_groq = bool(os.environ.get("GROQ_API_KEY"))
has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
st.caption(
    "AI keys found in this terminal: "
    f"Groq {'✅' if has_groq else '❌'}  |  Gemini {'✅' if has_gemini else '❌'}"
)

if not st.session_state.trades:
    st.write("Make some trades first, then come back here.")
else:
    if st.button("Get my coaching report", type="primary"):
        checked2 = check_trades(prices, st.session_state.trades, plan_signals, last)
        off2 = checked2[checked2["Followed plan?"] != "Yes"]
        score2 = (len(checked2) - len(off2)) / len(checked2) * 100
        facts = {
            "plan_name": plan_info["name"],
            "plan_buys_when": plan_info["buy_when"],
            "plan_sells_when": plan_info["sell_when"],
            "days_played": last + 1,
            "your_final_value": round(float(mine.iloc[-1])),
            "plan_final_value": round(float(plan.iloc[-1])),
            "buy_and_hold_final_value": round(float(hold.iloc[-1])),
            "total_trades": len(checked2),
            "off_plan_trades": len(off2),
            "discipline_score_percent": round(score2),
            "off_plan_trade_list": off2.head(10).to_dict("records"),
        }
        with st.spinner("Your coach is thinking (this can take up to a minute)..."):
            st.session_state.coach = get_coaching(facts, RULES)

    coach = st.session_state.get("coach")
    if coach:
        st.write(coach["explanation"])

        st.subheader("Rules suggested for you")
        for r in coach["rules"]:
            st.write("- " + RULES[r])

        better, blocked = replay_with_rules(
            prices, stocks, st.session_state.trades, START_CASH, last, coach["rules"]
        )

        st.subheader("Before and after")
        compare = pd.DataFrame(
            {
                "Your real trades": mine.values,
                "Your trades with the rules": better.values,
            },
            index=prices["Day"].iloc[: last + 1],
        )
        if not blocked:
            st.info(
                "None of your trades broke these rules, so both lines are identical "
                "and sit on top of each other. Try a round with a panic sell or "
                "a chase-the-rise buy to see the difference."
            )
        st.line_chart(compare)

        b1, b2, b3 = st.columns(3)
        b1.metric("Without rules", f"₹{mine.iloc[-1]:,.0f}")
        b2.metric("With rules", f"₹{better.iloc[-1]:,.0f}")
        diff = better.iloc[-1] - mine.iloc[-1]
        b3.metric("Difference", f"₹{diff:,.0f}")

        if diff > 0:
            st.success("In this round, following these rules would have helped you.")
        else:
            st.warning(
                "In this round, these rules would not have helped. That is useful to know too."
            )

        if blocked:
            with st.expander("Trades the rules would have blocked"):
                st.dataframe(pd.DataFrame(blocked), hide_index=True)

# ---------- THE BIG REVEAL ----------
if st.session_state.day == len(prices) - 1:
    st.divider()
    st.header("The big reveal")
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