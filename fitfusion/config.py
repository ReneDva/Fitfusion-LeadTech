"""FitFusion brand constants and app-wide config."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
DB_PATH = ROOT_DIR / "fitfusion.db"

load_dotenv(ROOT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_ENABLED = bool(OPENAI_API_KEY) and not OPENAI_API_KEY.startswith("sk-your-key")

# Brand palette
GOLD = "#F4B223"
BLUE = "#4CB7C5"
GREEN = "#8BC53F"
BG = "#090909"
CARD_BG = "#151515"
BG_SECONDARY = "#1F1F1F"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B3B3B3"

APP_NAME = "FitFusion"
SLOGAN = {
    "en": "Eat Smart • Train Right • Live Strong",
    "ar": "كُل بذكاء • تمرّن بصواب • عِش بقوة",
    "he": "אכלו בחכמה • התאמנו נכון • חיו בעוצמה",
}

SUPPORTED_LANGUAGES = {
    "en": {"label": "English", "flag": "🇺🇸", "dir": "ltr"},
    "ar": {"label": "العربية", "flag": "🇸🇦", "dir": "rtl"},
    "he": {"label": "עברית", "flag": "🇮🇱", "dir": "rtl"},
}

DEFAULT_LANGUAGE = "en"

ACTIVITY_LEVELS = ["sedentary", "light", "moderate", "active", "very_active"]
FITNESS_GOALS = ["lose_weight", "build_muscle", "maintain", "improve_endurance", "general_health"]
DIETARY_PREFERENCES = ["none", "vegetarian", "vegan", "keto", "paleo", "halal", "kosher", "gluten_free"]
EXPERIENCE_LEVELS = ["beginner", "intermediate", "advanced"]
WORKOUT_LOCATIONS = ["home", "gym", "outdoor"]
