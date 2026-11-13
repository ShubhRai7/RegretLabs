import pandas as pd


def buy_and_hold(prices, stocks, start_cash):
    """Buy equal amounts of every stock on Day 1 and never touch them."""
    first_prices = prices.loc[0, stocks]
    shares = (start_cash / len(stocks)) / first_prices
    return (prices[stocks] * shares).sum(axis=1)


def buy_the_dip(prices, stocks, start_cash, dip=0.05, target=0.05, window=10):
    """
    The plan on autopilot.
    Buy a stock when its price falls 5% below its highest price of the last
    10 days. Sell it when it rises 5% above what we paid.
    """
    slot = start_cash / len(stocks)  # money set aside for each stock
    cash = start_cash
    shares = {s: 0.0 for s in stocks}
    paid = {s: 0.0 for s in stocks}
    values = []
    signals = []

    for i in range(len(prices)):
        for s in stocks:
            price = float(prices.loc[i, s])
            recent_high = float(prices.loc[max(0, i - window):i, s].max())

            if shares[s] == 0:
                if price <= recent_high * (1 - dip) and cash >= slot:
                    shares[s] = slot / price
                    cash -= slot
                    paid[s] = price
                    signals.append({"day": i + 1, "stock": s, "action": "BUY"})
            else:
                if price >= paid[s] * (1 + target):
                    cash += shares[s] * price
                    shares[s] = 0.0
                    signals.append({"day": i + 1, "stock": s, "action": "SELL"})

        total = cash + sum(shares[s] * float(prices.loc[i, s]) for s in stocks)
        values.append(total)

    return pd.Series(values, index=prices.index), signals


def player_values(prices, stocks, trades, start_cash, last_index):
    """Rebuild the player's total value for every day, from their trade record."""
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


def check_trades(prices, trades, signals, last_index, tolerance=3, lookahead=10):
    """Mark each of the player's trades as on-plan or off-plan."""
    rows = []
    for t in trades:
        followed = any(
            s["stock"] == t["stock"]
            and s["action"] == t["action"]
            and abs(s["day"] - t["day"]) <= tolerance
            for s in signals
        )
        # What happened to this trade over the next 10 revealed days
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


def missed_signals(trades, signals, last_index, tolerance=3):
    """Moments when the plan acted but the player did nothing."""
    missed = []
    for s in signals:
        if s["day"] - 1 > last_index:
            continue  # this day has not been played yet
        matched = any(
            t["stock"] == s["stock"]
            and t["action"] == s["action"]
            and abs(t["day"] - s["day"]) <= tolerance
            for t in trades
        )
        if not matched:
            missed.append(s)
    return pd.DataFrame(missed)