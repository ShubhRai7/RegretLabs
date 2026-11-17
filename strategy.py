import numpy as np
import pandas as pd


# ----------------------------------------------------------------------
# A tiny pretend portfolio that every plan uses to trade on its own
# ----------------------------------------------------------------------
class _Sim:
    def __init__(self, stocks, start_cash):
        self.stocks = stocks
        self.cash = float(start_cash)
        self.shares = {s: 0.0 for s in stocks}
        self.paid = {s: 0.0 for s in stocks}
        self.peak = {s: 0.0 for s in stocks}
        self.signals = []
        self.values = []

    def held(self, stock):
        return self.shares[stock] > 0

    def buy(self, stock, amount, price, day):
        amount = min(amount, self.cash)
        if amount <= 0.01:
            return False
        self.shares[stock] += amount / price
        self.cash -= amount
        self.paid[stock] = price
        self.peak[stock] = price
        self.signals.append({"day": day, "stock": stock, "action": "BUY"})
        return True

    def sell(self, stock, price, day):
        if not self.held(stock):
            return False
        self.cash += self.shares[stock] * price
        self.shares[stock] = 0.0
        self.signals.append({"day": day, "stock": stock, "action": "SELL"})
        return True

    def record(self, px, i):
        total = self.cash + sum(self.shares[s] * px[s][i] for s in self.stocks)
        self.values.append(total)


def _prep(prices, stocks):
    return {s: prices[s].to_numpy(dtype=float) for s in stocks}


def _finish(prices, sim):
    return pd.Series(sim.values, index=prices.index), sim.signals


# ----------------------------------------------------------------------
# The baseline: buy equal amounts on Day 1 and never touch them
# ----------------------------------------------------------------------
def buy_and_hold(prices, stocks, start_cash):
    first_prices = prices.loc[0, stocks]
    shares = (start_cash / len(stocks)) / first_prices
    return (prices[stocks] * shares).sum(axis=1)


# ----------------------------------------------------------------------
# PLAN 1: Buy the Dip
# ----------------------------------------------------------------------
def buy_the_dip(prices, stocks, start_cash, dip=0.05, target=0.05, window=10):
    px = _prep(prices, stocks)
    sim = _Sim(stocks, start_cash)
    slot = start_cash / len(stocks)

    for i in range(len(prices)):
        day = i + 1
        for s in stocks:
            price = px[s][i]
            if not sim.held(s):
                recent_high = px[s][max(0, i - window): i + 1].max()
                if price <= recent_high * (1 - dip) and sim.cash >= slot * 0.99:
                    sim.buy(s, slot, price, day)
            else:
                if price >= sim.paid[s] * (1 + target):
                    sim.sell(s, price, day)
        sim.record(px, i)
    return _finish(prices, sim)


# ----------------------------------------------------------------------
# PLAN 2: Follow the Trend
# ----------------------------------------------------------------------
def follow_the_trend(prices, stocks, start_cash, short=10, long=30):
    px = _prep(prices, stocks)
    sim = _Sim(stocks, start_cash)
    slot = start_cash / len(stocks)

    for i in range(len(prices)):
        day = i + 1
        if i >= long - 1:
            for s in stocks:
                short_avg = px[s][i - short + 1: i + 1].mean()
                long_avg = px[s][i - long + 1: i + 1].mean()
                bullish = short_avg > long_avg
                if bullish and not sim.held(s) and sim.cash >= slot * 0.99:
                    sim.buy(s, slot, px[s][i], day)
                elif not bullish and sim.held(s):
                    sim.sell(s, px[s][i], day)
        sim.record(px, i)
    return _finish(prices, sim)


# ----------------------------------------------------------------------
# PLAN 3: Chase the Winners
# ----------------------------------------------------------------------
def chase_the_winners(prices, stocks, start_cash, every=10, lookback=10, keep=2):
    px = _prep(prices, stocks)
    sim = _Sim(stocks, start_cash)

    for i in range(len(prices)):
        day = i + 1
        if i >= lookback and i % every == 0:
            gains = {s: px[s][i] / px[s][i - lookback] - 1 for s in stocks}
            winners = sorted(stocks, key=lambda s: gains[s], reverse=True)[:keep]
            for s in stocks:
                if s not in winners and sim.held(s):
                    sim.sell(s, px[s][i], day)
            to_buy = [s for s in winners if not sim.held(s)]
            if to_buy:
                share = sim.cash / len(to_buy)
                for s in to_buy:
                    sim.buy(s, share, px[s][i], day)
        sim.record(px, i)
    return _finish(prices, sim)


# ----------------------------------------------------------------------
# PLAN 4: Monthly Investing
# ----------------------------------------------------------------------
def monthly_investing(prices, stocks, start_cash, every=20):
    px = _prep(prices, stocks)
    sim = _Sim(stocks, start_cash)
    instalments = int(np.ceil(len(prices) / every))
    per_stock = (start_cash / instalments) / len(stocks)

    for i in range(len(prices)):
        day = i + 1
        if i % every == 0:
            for s in stocks:
                sim.buy(s, per_stock, px[s][i], day)
        sim.record(px, i)
    return _finish(prices, sim)


# ----------------------------------------------------------------------
# PLAN 5: Breakout and Protect
# ----------------------------------------------------------------------
def breakout_and_protect(prices, stocks, start_cash, lookback=20, protect=0.05):
    px = _prep(prices, stocks)
    sim = _Sim(stocks, start_cash)
    slot = start_cash / len(stocks)

    for i in range(len(prices)):
        day = i + 1
        for s in stocks:
            price = px[s][i]
            if sim.held(s):
                sim.peak[s] = max(sim.peak[s], price)
                if price <= sim.peak[s] * (1 - protect):
                    sim.sell(s, price, day)
            elif i >= lookback:
                prior_high = px[s][i - lookback: i].max()
                if price > prior_high and sim.cash >= slot * 0.99:
                    sim.buy(s, slot, price, day)
        sim.record(px, i)
    return _finish(prices, sim)


# ----------------------------------------------------------------------
# The menu of plans, with the full details shown in the app
# ----------------------------------------------------------------------
STRATEGIES = {
    "dip": {
        "name": "Buy the Dip",
        "tagline": "Buy a stock after it falls 5%, sell after a 5% gain",
        "buy_when": "A stock's price falls 5% or more below its highest price of the last 10 days.",
        "sell_when": "The price rises 5% above what the plan paid for it.",
        "money": "The money is split into 5 equal parts, one per stock. Each part buys one stock at a time.",
        "style": "Patient bargain hunter. Waits for prices to drop, then takes small profits.",
        "best_when": "Markets that bounce up and down, where drops usually recover.",
        "struggles_when": "A stock that keeps falling, because the plan has no safety exit and holds until it recovers.",
        "run": buy_the_dip,
    },
    "trend": {
        "name": "Follow the Trend",
        "tagline": "Buy when the 10-day average rises above the 30-day average",
        "buy_when": "A stock's average price over the last 10 days moves above its average over the last 30 days. The plan cannot act before Day 30, because it needs 30 days of history first.",
        "sell_when": "The 10-day average drops back below the 30-day average.",
        "money": "The money is split into 5 equal parts, one per stock.",
        "style": "Goes with the flow. Rides stocks that are rising and leaves the ones that are falling.",
        "best_when": "Long, steady rises (or falls, because it steps out of a falling stock).",
        "struggles_when": "Sudden reversals, because averages react late: it buys a bit late and sells a bit late.",
        "run": follow_the_trend,
    },
    "winners": {
        "name": "Chase the Winners",
        "tagline": "Every 10 days, hold only the 2 stocks that rose the most",
        "buy_when": "Every 10 days (from Day 11), the plan ranks the stocks by how much they rose over the last 10 days and buys the top 2 it does not already own.",
        "sell_when": "A stock that drops out of the top 2 is sold at the next 10-day check.",
        "money": "Cash is shared equally between the new picks.",
        "style": "Loves momentum. Backs whatever is hot right now.",
        "best_when": "Markets where winners keep winning for a while.",
        "struggles_when": "Sudden reversals, when last period's winner becomes the next period's loser.",
        "run": chase_the_winners,
    },
    "monthly": {
        "name": "Monthly Investing",
        "tagline": "Put the same amount into every stock every 20 days, never sell",
        "buy_when": "Every 20 trading days, starting on Day 1, it spends an equal slice of the total money, split equally across all 5 stocks.",
        "sell_when": "Never. It holds everything until the end.",
        "money": "The money is split into equal instalments, so part of it stays as cash until its turn.",
        "style": "Boring and steady. No predictions and no emotions.",
        "best_when": "Long-term rises, and bumpy markets, because buying in small steps smooths out the price you pay.",
        "struggles_when": "Fast early rallies, because most of the money is not invested yet.",
        "run": monthly_investing,
    },
    "breakout": {
        "name": "Breakout and Protect",
        "tagline": "Buy a new 20-day high, sell if it falls 5% from its peak",
        "buy_when": "A stock's price is higher than its highest price of the previous 20 days (a 'breakout'). The plan cannot act before Day 21.",
        "sell_when": "The price falls 5% below its highest point since the plan bought it (a 'trailing stop').",
        "money": "The money is split into 5 equal parts, one per stock.",
        "style": "Bold, but with a safety net. Buys strength and cuts losses quickly.",
        "best_when": "Strong rises that keep going, and sharp crashes, because it exits early.",
        "struggles_when": "Choppy markets with false breakouts, where it buys a high and sells after a small fall.",
        "run": breakout_and_protect,
    },
}


def run_plan(plan_id, prices, stocks, start_cash):
    """Run the chosen plan on autopilot. Returns (daily values, list of buy/sell signals)."""
    return STRATEGIES[plan_id]["run"](prices, stocks, start_cash)


# ----------------------------------------------------------------------
# Rebuild the player's total value for every day from their trade record
# ----------------------------------------------------------------------
def player_values(prices, stocks, trades, start_cash, last_index):
    cash = start_cash
    shares = {s: 0 for s in stocks}
    values = []

    for i in range(last_index + 1):
        for t in trades:
            if t["day"] == i + 1:
                cost = t["quantity"] * t["price"]
                if t["action"] == "BUY":
                    cash -= cost
                    shares[t["stock"]] += t["quantity"]
                else:
                    cash += cost
                    shares[t["stock"]] -= t["quantity"]
        values.append(cash + sum(shares[s] * float(prices.loc[i, s]) for s in stocks))

    return pd.Series(values)


# ----------------------------------------------------------------------
# Mark each of the player's trades as on-plan or off-plan
# ----------------------------------------------------------------------
def check_trades(prices, trades, signals, last_index, tolerance=3, lookahead=10):
    rows = []
    for t in trades:
        followed = any(
            s["stock"] == t["stock"]
            and s["action"] == t["action"]
            and abs(s["day"] - t["day"]) <= tolerance
            for s in signals
        )
        later_i = min(t["day"] - 1 + lookahead, last_index)
        later_price = float(prices.loc[later_i, t["stock"]])
        result = (later_price - t["price"]) * t["quantity"]
        if t["action"] == "SELL":
            result = -result  # selling is good if the price went down after
        rows.append(
            {
                "Day": t["day"],
                "Stock": t["stock"],
                "Action": t["action"],
                "Quantity": t["quantity"],
                "Price": t["price"],
                "Followed plan?": "Yes" if followed else "No - off plan",
                "Result after 10 days (Rs)": round(result),
            }
        )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Moments when the plan acted but the player did nothing
# ----------------------------------------------------------------------
def missed_signals(trades, signals, last_index, tolerance=3):
    missed = []
    for s in signals:
        if s["day"] - 1 > last_index:
            continue
        matched = any(
            t["stock"] == s["stock"]
            and t["action"] == s["action"]
            and abs(t["day"] - s["day"]) <= tolerance
            for t in trades
        )
        if not matched:
            missed.append(s)
    return pd.DataFrame(missed)