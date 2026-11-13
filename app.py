import streamlit as st
import pandas as pd

st.set_page_config(page_title="Regret Replay", layout="wide")

prices = pd.read_csv("data/prices_period1.csv")
stocks = [c for c in prices.columns if c != "Day"]
START_CASH = 100000

# Set up a fresh game the first time the page loads
if "day" not in st.session_state:
    st.session_state.day = 0
    st.session_state.cash = START_CASH
    st.session_state.shares = {s: 0 for s in stocks}
    st.session_state.trades = []
    st.session_state.msg = ""


def price_today(stock):
    return float(prices.loc[st.session_state.day, stock])


def holdings_value():
    return sum(st.session_state.shares[s] * price_today(s) for s in stocks)


def next_day():
    if st.session_state.day < len(prices) - 1:
        st.session_state.day += 1
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
        }
    )
    st.session_state.msg = f"Done: {action} {qty} of {stock} at ₹{price:,.2f}"


st.title("Regret Replay")
st.caption("Pretend money. Real market history, with names and dates hidden.")

day_number = int(prices.loc[st.session_state.day, "Day"])
total = st.session_state.cash + holdings_value()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Day", f"{day_number} of {len(prices)}")
c2.metric("Cash", f"₹{st.session_state.cash:,.0f}")
c3.metric("Shares worth", f"₹{holdings_value():,.0f}")
c4.metric("Total value", f"₹{total:,.0f}")

st.subheader("Prices so far")
st.line_chart(prices.set_index("Day").iloc[: st.session_state.day + 1])

st.subheader("Your move")
a, b, c, d = st.columns([2, 1, 1, 1])
a.selectbox("Stock", stocks, key="sel_stock")
b.number_input("How many shares", min_value=1, value=10, step=1, key="qty")
c.button("Buy", on_click=trade, args=("BUY",), use_container_width=True)
d.button("Sell", on_click=trade, args=("SELL",), use_container_width=True)

if st.session_state.msg:
    st.info(st.session_state.msg)

st.button("Next Day ➜", on_click=next_day, type="primary")

if st.session_state.day == len(prices) - 1:
    st.success("The period is over. Final value: ₹{:,.0f}".format(total))

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

# ---------- RESULTS ----------
from strategy import buy_and_hold, buy_the_dip, player_values


def skip_ten():
    st.session_state.day = min(st.session_state.day + 10, len(prices) - 1)
    st.session_state.msg = ""


st.button("Fast-forward 10 days (for testing)", on_click=skip_ten)

st.divider()
st.header("Results so far")

last = st.session_state.day
mine = player_values(prices, stocks, st.session_state.trades, START_CASH, last)
hold = buy_and_hold(prices, stocks, START_CASH).iloc[: last + 1]
plan, plan_signals = buy_the_dip(prices, stocks, START_CASH)
plan = plan.iloc[: last + 1]

chart = pd.DataFrame(
    {
        "You": mine.values,
        "Plan on autopilot (buy the dip)": plan.values,
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
from strategy import check_trades, missed_signals

st.divider()
st.header("Did you follow the plan?")

with st.expander("See what the plan did on autopilot"):
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

    m1, m2, m3 = st.columns(3)
    m1.metric("Discipline score", f"{score:.0f}%")
    m2.metric("Off-plan trades", f"{len(off)} of {len(checked)}")
    m3.metric(
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
import json
from ai import get_coaching
from rules import RULES, replay_with_rules

st.divider()
st.header("Your coaching report")

if not st.session_state.trades:
    st.write("Make some trades first, then come back here.")
else:
    if st.button("Get my coaching report", type="primary"):
        checked2 = check_trades(prices, st.session_state.trades, plan_signals, last)
        off2 = checked2[checked2["Followed plan?"] != "Yes"]
        score2 = (len(checked2) - len(off2)) / len(checked2) * 100
        facts = {
            "days_played": last + 1,
            "your_final_value": round(float(mine.iloc[-1])),
            "plan_final_value": round(float(plan.iloc[-1])),
            "buy_and_hold_final_value": round(float(hold.iloc[-1])),
            "total_trades": len(checked2),
            "off_plan_trades": len(off2),
            "discipline_score_percent": round(score2),
            "off_plan_trade_list": off2.head(10).to_dict("records"),
        }
        with st.spinner("Your coach is thinking..."):
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

        st.subheader("Before and after")        #<- same column
        compare = pd.DataFrame(                 #<- same column
            {
                "Your real trades": mine.values,
                "Your trades with the rules": better.values,
            },
            index=prices["Day"].iloc[: last + 1],
        )
        if not blocked:                         #<- same column
            st.info(
                "None of your trades broke these rules, so both lines are identical "
                "and sit on top of each other. Try a round with a panic sell or "
                "a chase-the-rise buy to see the difference."
            )
        st.line_chart(compare)                  #<- same column

        b1, b2, b3 = st.columns(3)
        b1.metric("Without rules", f"₹{mine.iloc[-1]:,.0f}")
        b2.metric("With rules", f"₹{better.iloc[-1]:,.0f}")
        diff = better.iloc[-1] - mine.iloc[-1]
        b3.metric("Difference", f"₹{diff:,.0f}")

        if diff > 0:
            st.success("In this round, following these rules would have helped you.")
        else:
            st.warning("In this round, these rules would not have helped. That is useful to know too.")

        if blocked:
            with st.expander("Trades the rules would have blocked"):
                st.dataframe(pd.DataFrame(blocked), hide_index=True)

# ---------- THE BIG REVEAL ----------
if st.session_state.day == len(prices) - 1:
    st.divider()
    st.header("The big reveal")
    with open("data/answer_key.json") as f:
        key_data = json.load(f)
    st.write(
        f"You were trading from **{key_data['dates'][0]}** to **{key_data['dates'][-1]}**."
    )
    for name, ticker in key_data["companies"].items():
        st.write(f"- {name} was **{ticker.replace('.NS', '')}**")