import pandas as pd

# The fixed menu of rules. The AI can only choose from this list.
RULES = {
    "no_panic_sell": "Do not sell a stock right after it has fallen 5% or more in the last 3 days.",
    "no_chasing": "Do not buy a stock right after it has risen 5% or more in the last 3 days.",
    "max_30_percent": "Never put more than 30% of your total money into one stock.",
}


def recent_change(prices, stock, i, days=3):
    now = float(prices.loc[i, stock])
    before = float(prices.loc[max(0, i - days), stock])
    return (now - before) / before


def replay_with_rules(prices, stocks, trades, start_cash, last_index, active_rules):
    """Replay the player's own decisions, skipping any trade a rule would block."""
    cash = start_cash
    shares = {s: 0 for s in stocks}
    blocked = []
    values = []

    for i in range(last_index + 1):
        day = i + 1
        for t in trades:
            if t["day"] != day:
                continue
            s = t["stock"]
            q = t["quantity"]
            price = t["price"]
            reason = None

            if t["action"] == "SELL":
                if "no_panic_sell" in active_rules and recent_change(prices, s, i) <= -0.05:
                    reason = RULES["no_panic_sell"]
                elif q > shares[s]:
                    reason = "Not enough shares left, because an earlier trade was blocked."
            else:
                total_now = cash + sum(
                    shares[x] * float(prices.loc[i, x]) for x in stocks
                )
                if "no_chasing" in active_rules and recent_change(prices, s, i) >= 0.05:
                    reason = RULES["no_chasing"]
                elif "max_30_percent" in active_rules and (shares[s] + q) * price > 0.30 * total_now:
                    reason = RULES["max_30_percent"]
                elif q * price > cash:
                    reason = "Not enough cash left, because an earlier trade was blocked."

            if reason:
                blocked.append(
                    {
                        "Day": day,
                        "Stock": s,
                        "Action": t["action"],
                        "Quantity": q,
                        "Why blocked": reason,
                    }
                )
                continue

            if t["action"] == "BUY":
                cash -= q * price
                shares[s] += q
            else:
                cash += q * price
                shares[s] -= q

        values.append(
            cash + sum(shares[x] * float(prices.loc[i, x]) for x in stocks)
        )

    return pd.Series(values), blocked