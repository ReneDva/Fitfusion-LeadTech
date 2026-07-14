"""Shared-key OpenAI integration: AI Coach chat, meal-photo recognition, body-analysis narrative.

One OPENAI_API_KEY (set by whoever runs this app) powers AI features for every local user —
per the product decision, users never enter their own key. When no key is configured the
app keeps working in a rule-based offline mode instead of breaking.
"""
import json

import streamlit as st

from fitfusion.config import OPENAI_API_KEY, OPENAI_MODEL, AI_ENABLED, SUPPORTED_LANGUAGES

COACH_SYSTEM_PROMPT = """You are the FitFusion AI Coach: a friendly, motivational, evidence-based
fitness and nutrition expert. Personality: warm, positive, professional, encouraging, never robotic.
Give practical, safe, evidence-based advice on fitness, nutrition, recipes, muscle gain, weight loss,
supplements, recovery, injuries, hydration and healthy lifestyle. Keep answers concise (under ~180 words)
unless the user asks for depth. Never diagnose medical conditions — recommend seeing a professional for
medical concerns. Always reply in the language: {language_name}. This is a natural, localized response,
not a literal translation."""


@st.cache_resource
def _client():
    if not AI_ENABLED:
        return None
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


def ai_enabled() -> bool:
    return AI_ENABLED


def _lang_name(lang_code: str) -> str:
    return SUPPORTED_LANGUAGES.get(lang_code, {}).get("label", "English")


def _offline_coach_reply(message: str, language: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["protein", "بروتين", "חלבון"]):
        reply = "Aim for roughly 1.6-2.2g of protein per kg of bodyweight daily, spread across 3-4 meals, to support muscle repair and growth."
    elif any(w in msg for w in ["weight loss", "lose weight", "خسارة", "ירידה"]):
        reply = "Sustainable weight loss comes from a modest calorie deficit (~15-20% below TDEE), a protein-rich diet, and consistent strength + cardio training."
    elif any(w in msg for w in ["sleep", "نوم", "שינה"]):
        reply = "Aim for 7-9 hours of quality sleep — it's one of the biggest levers for recovery, hormone balance and appetite control."
    elif any(w in msg for w in ["water", "hydration", "ماء", "מים"]):
        reply = "A good baseline is ~35ml of water per kg of bodyweight, more on training days or in hot climates."
    else:
        reply = "Great question! Focus on the fundamentals: consistent training, adequate protein, enough sleep, and staying hydrated — small consistent habits beat perfection."
    reply += "\n\n(Offline mode — set OPENAI_API_KEY in .env for full AI Coach responses.)"
    return reply


def chat_with_coach(message: str, history: list[dict], language: str = "en", user_context: str = "") -> str:
    """history: list of {"role": "user"|"assistant", "content": str}"""
    client = _client()
    if client is None:
        return _offline_coach_reply(message, language)

    system = COACH_SYSTEM_PROMPT.format(language_name=_lang_name(language))
    if user_context:
        system += f"\n\nWhat you know about this user: {user_context}"

    messages = [{"role": "system", "content": system}]
    messages += history[-20:]
    messages.append({"role": "user", "content": message})

    try:
        resp = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, temperature=0.7, max_tokens=500)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"The AI Coach hit a network/API error ({e}). Please try again in a moment."


def analyze_meal_photo(image_b64: str, language: str = "en") -> dict:
    """Returns nutrition dict from a base64-encoded food photo, or an 'error' key on failure."""
    client = _client()
    if client is None:
        return {"error": "offline"}

    prompt = f"""Identify the food/meal in this photo and estimate its nutrition for the visible portion.
Respond in {_lang_name(language)} for the "name" and "notes" fields only (numbers stay numeric).
Return strict JSON with keys: name, calories, protein, carbs, fat, fiber, sugar, sodium (mg),
quality_score (0-100 healthiness), notes (1 short sentence), healthier_alternative (1 short suggestion)."""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


def narrate_body_analysis(result: dict, language: str = "en") -> str:
    """Optional AI-written summary layered on top of the deterministic calculations."""
    client = _client()
    if client is None:
        return ""
    prompt = f"""Write a warm, motivational 2-3 sentence summary (in {_lang_name(language)}) of this user's
body analysis, highlighting their strongest positive and one clear next step. Data: {json.dumps(result)}"""
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""


def generate_recipe(ingredients_or_goal: str, dietary_preference: str = "none", language: str = "en") -> str:
    client = _client()
    if client is None:
        return "Recipe generation needs an OpenAI key. Set OPENAI_API_KEY in .env to enable this feature."
    prompt = f"""Create one healthy recipe (in {_lang_name(language)}) based on: "{ingredients_or_goal}".
Dietary preference: {dietary_preference}. Include a short ingredient list, steps, and approximate calories/macros.
Keep it under 200 words."""
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=500
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Couldn't generate a recipe right now ({e})."
