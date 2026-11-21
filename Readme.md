# Regret Replay — Shreemant
Trade smarter. Regret less.
An AI-coached practice-investing game built for the Arthaton 2026 AI FinTech hackathon.

Demo video: <YouTube link>

The problem
Most beginner investors don't lose money because their plan is bad. They lose it
because they abandon it: they panic-sell after a drop or chase stocks that have
already risen. Regret Replay measures that gap and puts a price on it.

What it does
1. Pick one of 5 real market scenarios (about 6 months each, from real NSE history).
   Company names are hidden as "Stock A–E" and dates as "Day 1, Day 2…", so
   hindsight can't help you.
2. Pick one of 5 plans: Buy the Dip, Follow the Trend, Chase the Winners,
   Monthly Investing, Breakout and Protect.
3. Trade with pretend ₹1,00,000, one day (or ten days) at a time. The app shows
   the order total before each trade and what your plan says to do today.
4. See your result against the same plan run by a robot and against plain buy-and-hold.
5. "Did you follow the plan?" gives a discipline score, lists every off-plan trade,
   shows what happened after each one, and lists the plan's moves you skipped.
6. The AI coach explains your habits in plain English and picks up to 3 rules
   from a fixed menu (no selling after a quick 5% drop, no buying after a quick
   5% rise, max 30% in one stock).
7. The app replays your same trades with those rules applied: before vs after.
8. The big reveal shows the real dates, a one-line story and the real companies.
9. "Watch the robot" page: no human plays; watch plans trade on their own.

How the AI is used (and not used)
- All numbers are calculated by the app's own code, never by the AI.
- The AI only explains the facts and chooses rules from a fixed menu.
- It never predicts prices or recommends stocks.
- If the AI can't be reached, the app shows a basic summary instead.

AI models and APIs used
- Groq API — model `openai/gpt-oss-120b` (primary coach)
- Google Gemini API — model `gemini-3.8-flash` (fallback)
- yfinance — one-off download of historical NSE prices (saved as CSV in /data)
- Claude (Anthropic) was used as an AI coding assistant while building this project.

Run it
1. Install Python 3.10+.
2. `pip install -r requirements.txt`
3. (Optional, for the AI coach)
   export GROQ_API_KEY="your key"
   export GEMINI_API_KEY="your key"
   Without keys the app still works and shows a basic summary.
4. `streamlit run "Your Laboratory.py"`

Data files are already in /data. To rebuild them: `python get_data.py`.

#Project structure
- `Your Laboratory.py` main game
- `pages/1_Watch_the_robot.py` robot-only page
- `strategy.py` the 5 plans and the plan check
- `rules.py` behaviour rules and replay
- `ai.py` Groq/Gemini coach
- `get_data.py` data builder
- `data/` price files, answer keys, scenario list

Limits
5 large stocks, 6-month windows, a simple discipline score. Simple plans often
don't beat buy-and-hold, and the app shows that openly. Prototype only.

Safety
Paper money and historical data only. No real trades, no bank details, no keys in this repo.
