<img width="1052" height="540" alt="image" src="https://github.com/user-attachments/assets/09d881d3-f1ca-4706-b4c2-698d10ec3f2e" /># Regret Replay — by Shreemant
**Trade smarter. Regret less.**

An AI-coached practice-investing game, built for the Arthaton 2026 AI FinTech hackathon.
Team RegretLabs · Built by Shreemant

🎥 Demo video: <YouTube link>

---

## The problem
Most beginner investors don't lose money because their strategy is bad. They lose it
because they abandon it: they panic-sell after a drop, or chase stocks that have already
risen. Regret Replay measures that gap and puts a price on it.

## Who it is for
First-time investors who want to learn from mistakes with no real money at risk.

## What the app does
1. **Pick a scenario.** Choose one of 5 real market periods (about 6 months each, from
   real NSE history). Company names are hidden as "Stock A–E" and dates as "Day 1, Day 2…",
   so hindsight can't help.
2. **Pick a plan.** Five clear rule-based plans: Buy the Dip, Follow the Trend,
   Chase the Winners, Monthly Investing, Breakout and Protect.
3. **Play.** Trade with pretend ₹1,00,000, one day or ten days at a time. The app shows
   the order total before each trade, and what your plan says to do today.
4. **Compare.** See your result against the same plan run by a robot, and against
   plain buy-and-hold.
5. **Did you follow the plan?** A discipline score, a list of off-plan trades, what
   happened after each one, and the plan's moves you skipped.
6. **AI coach.** Explains your habits in plain English and picks up to 3 rules from a
   fixed menu (no selling after a quick 5% drop, no buying after a quick 5% rise,
   max 30% of money in one stock).
7. **Before vs after.** Replays your same trades with those rules applied.
8. **Big reveal.** Shows the real dates, a one-line story, and the real companies.
9. **Watch the robot.** A second page where no human plays: pick plans and watch
   them trade on their own.

## How the AI is used (and how it is not)
- Every number is calculated by the app's own Python code.
- The AI only explains those facts and picks rules from a fixed menu.
- It never predicts prices, never calculates results and never recommends stocks.
- If no AI service can be reached, the app still works and shows a basic summary.

## AI models, APIs and data sources
| What | Provider | Used for |
|---|---|---|
| `openai/gpt-oss-120b` via the Groq API (console.groq.com) | Groq | Primary AI coach |
| `gemini-3.8-flash` via the Google Gemini API (aistudio.google.com) | Google | Backup AI coach if Groq fails |
| Historical NSE prices via the `yfinance` library | Yahoo Finance data | One-time download of price history, saved as CSV in `/data` |
| Claude | Anthropic | AI consultant and coding assistant (see below) |

### AI assistance disclosure
We used **Claude (by Anthropic)** as a consulting and coding assistant while building
this project: for discussing the idea, planning the structure, helping write and debug
code, and explaining finance concepts to a team new to the stock market. The team ran,
tested and chose what went into the final project.

## Run it
1. Install Python 3.10 or newer.
2. Install the libraries:
   `pip install streamlit pandas numpy yfinance groq google-genai`
3. Start the app:
   `streamlit run "Your Laboratory.py"`

The price data is already included in `/data`, so no download is needed.

### Optional: turn on the AI coach
The app reads the AI keys from environment variables named `GROQ_API_KEY` and
`GEMINI_API_KEY`. Set them in your own environment (for example as GitHub Codespaces
secrets, or in your shell profile). **Keys are never stored in this repository.**
Without keys, everything else still works and the coach shows a basic summary.
Free keys can be created at console.groq.com and aistudio.google.com.

### Optional: rebuild the data
`python get_data.py` downloads the price history again and rebuilds the 5 scenarios.

## Project structure
- `Your Laboratory.py` — main game
- `pages/1_Watch_the_robot.py` — robot-only page
- `strategy.py` — the 5 plans and the plan check
- `rules.py` — behaviour rules and the replay with rules
- `ai.py` — Groq and Gemini coach
- `get_data.py` — builds the 5 scenarios
- `data/` — price files, answer keys, scenario list
- `.streamlit/config.toml` — dark theme settings

## Limits
5 large stocks, 6-month windows, one plan compared at a time, and a simple discipline
score. Simple plans often don't beat buy-and-hold, and the app shows that openly.
This is a prototype.

## Safety
Paper money and historical data only. No real trades, no bank details, no personal
data and no API keys in this repository. This is a learning tool, not investment advice.

## Contributors
Shubh Rai
Manav Parimal Kamdar
Renu Sri Nitya Gowravajjala
