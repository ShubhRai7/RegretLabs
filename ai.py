import os
import json
import time

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-3.8-flash"
TIMEOUT_SECONDS = 60


def _extract_json(text):
    """Pull the JSON out of the AI's reply, even if it adds extra words."""
    start = text.find("{")
    end = text.rfind("}")
    return json.loads(text[start : end + 1])


def _ask_groq(prompt, key):
    from groq import Groq

    client = Groq(api_key=key, timeout=TIMEOUT_SECONDS)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.choices[0].message.content)


def _ask_gemini(prompt, key):
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=TIMEOUT_SECONDS * 1000),
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return _extract_json(response.text)


def get_coaching(facts, rules_menu):
    default_rules = list(rules_menu.keys())
    simple_summary = (
        f"You made {facts['total_trades']} trades and {facts['off_plan_trades']} "
        f"went against your plan (discipline score {facts['discipline_score_percent']}%)."
    )

    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not groq_key and not gemini_key:
        return {
            "explanation": simple_summary + " (No AI key set, so this is a basic summary.)",
            "rules": default_rules,
        }

    menu_text = "\n".join(f"{k}: {v}" for k, v in rules_menu.items())
    prompt = f"""You are a friendly coach inside a pretend-money investing practice game.
A player traded through a past period. Their chosen plan, run on autopilot, is the comparison.
All numbers below were calculated by the app. Do not recalculate them, do not invent
numbers, and never recommend any stock. Only comment on how the player's behaviour
compared with their plan.

Write 3 to 4 sentences in simple everyday English, speaking to the player as "you".
Then choose up to 3 rule ids from the menu that best fit the mistakes you described.
Only use ids from the menu.

FACTS:
{json.dumps(facts, default=str)}

RULE MENU:
{menu_text}

Reply with only JSON, exactly like: {{"explanation": "...", "rules": ["id1", "id2"]}}"""

    # Try each available service in order. Groq first, because it is fast.
    attempts = []
    if groq_key:
        attempts.append(("Groq", _ask_groq, groq_key))
    if gemini_key:
        attempts.append(("Gemini", _ask_gemini, gemini_key))

    errors = []
    for round_number in range(2):
        for name, ask, key in attempts:
            try:
                data = ask(prompt, key)
                chosen = [r for r in data.get("rules", []) if r in rules_menu][:3]
                return {
                    "explanation": str(data.get("explanation", simple_summary)),
                    "rules": chosen or default_rules,
                }
            except Exception as e:
                errors.append(f"{name}: {e}")
        time.sleep(4)

    return {
        "explanation": simple_summary + f" (The AI could not be reached. {errors[-1]})",
        "rules": default_rules,
    }