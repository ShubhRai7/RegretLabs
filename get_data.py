import os
import json
import yfinance as yf

# Real companies, hidden behind anonymous names
companies = {
    "Stock A": "RELIANCE.NS",
    "Stock B": "TCS.NS",
    "Stock C": "HDFCBANK.NS",
    "Stock D": "INFY.NS",
    "Stock E": "ITC.NS",
}

os.makedirs("data", exist_ok=True)

# Feb to Jul 2020: the market crash and recovery
prices = yf.download(
    list(companies.values()),
    start="2020-02-01",
    end="2020-08-01",
    auto_adjust=True,
)["Close"]
prices = prices.dropna()

real_dates = [d.strftime("%Y-%m-%d") for d in prices.index]

# Replace real names with Stock A, B, C...
reverse = {ticker: name for name, ticker in companies.items()}
prices = prices.rename(columns=reverse)
prices = prices[sorted(prices.columns)].round(2)

# Replace real dates with Day 1, Day 2...
prices.insert(0, "Day", range(1, len(prices) + 1))
prices.to_csv("data/prices_period1.csv", index=False)

# Private answer sheet, revealed only at the end of the game
with open("data/answer_key.json", "w") as f:
    json.dump({"companies": companies, "dates": real_dates}, f, indent=2)

print("Done! Saved", len(prices), "days of prices.")
