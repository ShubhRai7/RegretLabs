import os
import json

# If you ever see an error about the model name, change this one line.
MODEL = "gemini-3.8-flash"


def get_coaching(facts, rules_menu):
    default_rules = list(rules_menu.keys())
    simple_summary = (
        f"You made {facts['total_trades']} trades and {facts['off_plan_trades']} "
        f"went against your plan (discipline score {facts['discipline_score_percent']}%)."
    )

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return {
            "explanation": simple_summary + " (AI key not set, so this is a basic summary.)",
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

Reply as JSON exactly like: {{"explanation": "...", "rules": ["id1", "id2"]}}"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=25000))
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = json.loads(response.text)
        chosen = [r for r in data.get("rules", []) if r in rules_menu][:3]
        return {
            "explanation": str(data.get("explanation", simple_summary)),
            "rules": chosen or default_rules,
        }
    except Exception as e:
        return {
            "explanation": simple_summary + f" (The AI could not be reached: {e})",
            "rules": default_rules,
        }