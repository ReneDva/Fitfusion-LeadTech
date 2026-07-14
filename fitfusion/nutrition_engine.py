"""Food search (local seed DB), barcode lookup (OpenFoodFacts public API), and meal scoring."""
import json

import requests

from fitfusion.config import DATA_DIR

with open(DATA_DIR / "foods.json", "r", encoding="utf-8") as f:
    FOODS = json.load(f)

OPENFOODFACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"


def search_food(query: str, limit: int = 10) -> list[dict]:
    """Matches against the English, Hebrew and Arabic names regardless of the UI language,
    so e.g. searching "עוף" finds Chicken Breast even when the app is in English."""
    query = (query or "").strip().lower()
    if not query:
        return FOODS[:limit]
    matches = []
    for f in FOODS:
        haystack = " ".join(filter(None, [f.get("name"), f.get("name_he"), f.get("name_ar")])).lower()
        if query in haystack:
            matches.append(f)
    return matches[:limit]


def display_name(food: dict, language: str = "en") -> str:
    return food.get(f"name_{language}") or food.get("name", "")


def scale_to_grams(food: dict, grams: float, language: str = "en") -> dict:
    factor = grams / 100.0
    nutrients = {k: round(v * factor, 1) for k, v in food["per_100g"].items()}
    nutrients["name"] = f"{display_name(food, language)} ({int(grams)}g)"
    return nutrients


def lookup_barcode(barcode: str) -> dict:
    """Queries the free OpenFoodFacts API. Returns {'error': ...} on any failure."""
    barcode = (barcode or "").strip()
    if not barcode.isdigit():
        return {"error": "invalid_barcode"}
    try:
        resp = requests.get(OPENFOODFACTS_URL.format(barcode=barcode), timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}

    if data.get("status") != 1:
        return {"error": "not_found"}

    product = data["product"]
    nutriments = product.get("nutriments", {})
    return {
        "name": product.get("product_name") or "Unknown product",
        "calories": nutriments.get("energy-kcal_100g", 0) or 0,
        "protein": nutriments.get("proteins_100g", 0) or 0,
        "carbs": nutriments.get("carbohydrates_100g", 0) or 0,
        "fat": nutriments.get("fat_100g", 0) or 0,
        "fiber": nutriments.get("fiber_100g", 0) or 0,
        "sugar": nutriments.get("sugars_100g", 0) or 0,
        "sodium": (nutriments.get("sodium_100g", 0) or 0) * 1000,
        "image_url": product.get("image_front_small_url", ""),
        "source": "openfoodfacts",
    }


def meal_quality_score(nutrients: dict) -> int:
    """0-100 heuristic: rewards protein/fiber density, penalizes sugar/sodium/fat density."""
    calories = max(nutrients.get("calories", 0), 1)
    protein = nutrients.get("protein", 0)
    fiber = nutrients.get("fiber", 0)
    sugar = nutrients.get("sugar", 0)
    sodium = nutrients.get("sodium", 0)
    fat = nutrients.get("fat", 0)

    score = 60
    score += min(protein * 4 / calories * 100, 20)
    score += min(fiber * 2, 10)
    score -= min(sugar * 1.5, 20)
    score -= min(sodium / 100, 15)
    score -= max(0, (fat * 9 / calories * 100) - 40) * 0.3
    return int(max(0, min(100, round(score))))


ALTERNATIVES = {
    "fast_food": "Swap for a grilled protein + whole grain + vegetables to cut sodium and fat.",
    "beverage": "Try sparkling water with fruit or unsweetened tea instead of sugary drinks.",
    "snack": "A handful of nuts or Greek yogurt gives you satiety with less sugar.",
}


def healthier_alternative(food: dict) -> str:
    return ALTERNATIVES.get(food.get("category", ""), "Pair this with a fiber-rich vegetable to balance the meal.")


def suggested_portion(food: dict, goal: str = "general_health") -> str:
    category = food.get("category", "")
    if category == "protein":
        return "120-180g" if goal == "build_muscle" else "100-150g"
    if category == "grain":
        return "80-150g (cooked)" if goal != "lose_weight" else "60-100g (cooked)"
    if category == "fat":
        return "15-30g"
    if category == "vegetable":
        return "150-250g — fill half your plate"
    if category == "fruit":
        return "1 medium serving (~120-150g)"
    return "Moderate portion"


def aggregate_meal(items: list[dict]) -> dict:
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
    names = []
    for item in items:
        for key in totals:
            totals[key] += item.get(key, 0)
        names.append(item.get("name", "item"))
    totals["name"] = " + ".join(names) if names else "Meal"
    totals["quality_score"] = meal_quality_score(totals)
    return totals
