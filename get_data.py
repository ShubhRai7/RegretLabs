import json
import os
import random

import pandas as pd
import yfinance as yf

# ----------------------------------------------------------------------
# SETTINGS you can change
# ----------------------------------------------------------------------
# Five big, old companies, so they all existed in every period below
COMPANIES = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS"]

# Make every stock start at 100, so players can't guess a company
# from its price level (for example, "this one costs 2000, it must be TCS")
REBASE_TO_100 = True

# The five periods. The "story" is only shown at the end of the game.
PERIODS = [
    {"start": "2020-02-01", "end": "2020-08-01",
     "story": "The 2020 crash and recovery: a very sharp fall, then a fast bounce back."},
    {"start": "2021-01-01", "end": "2021-07-01",
     "story": "Early 2021: markets climbing after the crash, with a few wobbles."},
    {"start": "2022-01-01", "end": "2022-07-01",
     "story": "First half of 2022: a rough, choppy stretch with a lot of ups and downs."},
    {"start": "2018-09-01", "end": "2019-03-01",
     "story": "Late 2018 into 2019: a nervous, bumpy market after a credit scare."},
    {"start": "2023-07-01", "end": "2024-01-01",
     "story": "Late 2023: a steady, confident climb."},
]

MIN_DAYS = 100  # skip a period if it has fewer trading days than this

# ----------------------------------------------------------------------
# 1. Download everything ONCE (one download is more reliable than five)
# ----------------------------------------------------------------------
os.makedirs("data", exist_ok=True)

first_day = min(p["start"] for p in PERIODS)
last_day = max(p["end"] for p in PERIODS)

print("Downloading prices. This can take up to a minute...")
raw = yf.download(
    COMPANIES,
    start=first_day,
    end=last_day,
    auto_adjust=True,
    progress=False,
)["Close"]

if raw.empty:
    raise SystemExit("Nothing was downloaded. Check the internet connection and try again.")

# ----------------------------------------------------------------------
# 2. Cut out each period, hide the names and dates, and save
# ----------------------------------------------------------------------
saved = []

for number, p in enumerate(PERIODS, start=1):
    chunk = raw.loc[p["start"]: p["end"]].dropna()

    if len(chunk) < MIN_DAYS:
        print(f"Period {number}: only {len(chunk)} days of clean data, so it was SKIPPED.")
        continue

    real_dates = [d.strftime("%Y-%m-%d") for d in chunk.index]

    # Give the companies anonymous names in a random (but repeatable) order
    order = COMPANIES[:]
    random.Random(number).shuffle(order)
    letters = ["Stock A", "Stock B", "Stock C", "Stock D", "Stock E"]
    mapping = {letters[i]: order[i] for i in range(len(order))}

    table = chunk.rename(columns={t: n for n, t in mapping.items()})
    table = table[sorted(table.columns)]

    if REBASE_TO_100:
        table = table / table.iloc[0] * 100
    table = table.round(2)

    # Replace real dates with Day 1, Day 2, ...
    table.insert(0, "Day", range(1, len(table) + 1))

    prices_file = f"prices_period{number}.csv"
    key_file = f"answer_key_period{number}.json"

    table.to_csv(f"data/{prices_file}", index=False)

    # The sealed envelope, opened only at the end of the game
    with open(f"data/{key_file}", "w") as f:
        json.dump(
            {"companies": mapping, "dates": real_dates, "story": p["story"]},
            f,
            indent=2,
        )

    # Keep the old file name working for Period 1, so nothing breaks
    if number == 1:
        with open("data/answer_key.json", "w") as f:
            json.dump(
                {"companies": mapping, "dates": real_dates, "story": p["story"]},
                f,
                indent=2,
            )

    # A simple sanity number: how did "buy equal amounts of everything" do?
    basket_move = (table[letters].iloc[-1] / table[letters].iloc[0] - 1).mean() * 100
    saved.append(
        {
            "number": number,
            "prices_file": prices_file,
            "key_file": key_file,
            "days": len(table),
        }
    )
    print(f"Period {number}: saved {len(table)} days. Buying everything on Day 1 would have moved {basket_move:+.1f}%.")

# ----------------------------------------------------------------------
# 3. A small list of the periods, for the game's dropdown
# ----------------------------------------------------------------------
with open("data/periods.json", "w") as f:
    json.dump({"periods": saved}, f, indent=2)

print()
print(f"Done! {len(saved)} of {len(PERIODS)} periods saved in the data folder.")