"""Shared-key Google Gemini integration: AI Coach chat, meal-photo recognition, body-analysis narrative.

One GEMMINI_API_KEY (set by whoever runs this app, using the free Gemini API tier) powers AI
features for every local user — per the product decision, users never enter their own key.
When no key is configured the app keeps working in a rule-based offline mode instead of breaking.
"""
import json

import streamlit as st

from fitfusion.config import GEMINI_API_KEY, GEMINI_MODEL, AI_ENABLED, SUPPORTED_LANGUAGES

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
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


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
    reply += "\n\n(Offline mode — set GEMMINI_API_KEY in .env for full AI Coach responses.)"
    return reply


def _to_gemini_history(history: list[dict]):
    from google.genai import types
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    return contents


def chat_with_coach(message: str, history: list[dict], language: str = "en", user_context: str = "") -> str:
    """history: list of {"role": "user"|"assistant", "content": str}"""
    client = _client()
    if client is None:
        return _offline_coach_reply(message, language)

    from google.genai import types

    system = COACH_SYSTEM_PROMPT.format(language_name=_lang_name(language))
    if user_context:
        system += f"\n\nWhat you know about this user: {user_context}"

    contents = _to_gemini_history(history[-20:])
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system, temperature=0.7, max_output_tokens=500),
        )
        return (resp.text or "").strip()
    except Exception as e:
        return f"The AI Coach hit a network/API error ({e}). Please try again in a moment."


def analyze_meal_photo(image_bytes: bytes, language: str = "en") -> dict:
    """Returns nutrition dict from a food photo (raw bytes), or an 'error' key on failure."""
    client = _client()
    if client is None:
        return {"error": "offline"}

    from google.genai import types

    prompt = f"""Identify the food/meal in this photo and estimate its nutrition for the visible portion.
Respond in {_lang_name(language)} for the "name" and "notes" fields only (numbers stay numeric).
Return strict JSON with keys: name, calories, protein, carbs, fat, fiber, sugar, sodium (mg),
quality_score (0-100 healthiness), notes (1 short sentence), healthier_alternative (1 short suggestion)."""

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3, max_output_tokens=500),
        )
        return json.loads(resp.text)
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
        from google.genai import types
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(temperature=0.6, max_output_tokens=200),
        )
        return (resp.text or "").strip()
    except Exception:
        return ""


def generate_recipe(ingredients_or_goal: str, dietary_preference: str = "none", language: str = "en") -> str:
    client = _client()
    if client is None:
        return "Recipe generation needs a Gemini key. Set GEMMINI_API_KEY in .env to enable this feature."
    prompt = f"""Create one healthy recipe (in {_lang_name(language)}) based on: "{ingredients_or_goal}".
Dietary preference: {dietary_preference}. Include a short ingredient list, steps, and approximate calories/macros.
Keep it under 200 words."""
    try:
        from google.genai import types
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=500),
        )
        return (resp.text or "").strip()
    except Exception as e:
        return f"Couldn't generate a recipe right now ({e})."
