"""Evidence-based formulas for body analysis. No black box — every number traces to a named formula.

References: Mifflin-St Jeor (BMR), Deurenberg (body-fat estimate from BMI),
WHO BMI healthy range, ISSN protein guidelines.
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_ADJUSTMENT = {
    "lose_weight": -0.20,
    "build_muscle": 0.12,
    "maintain": 0.0,
    "improve_endurance": 0.05,
    "general_health": 0.0,
}


def bmi(weight_kg: float, height_cm: float) -> float:
    h_m = height_cm / 100
    return round(weight_kg / (h_m * h_m), 1)


def healthy_weight_range(height_cm: float) -> tuple[float, float]:
    h_m = height_cm / 100
    return round(18.5 * h_m * h_m, 1), round(24.9 * h_m * h_m, 1)


def body_fat_estimate(bmi_value: float, age: int, gender: str, body_fat_pct: float = None) -> float:
    """User-provided value wins; otherwise Deurenberg formula estimate."""
    if body_fat_pct:
        return round(body_fat_pct, 1)
    sex = 1 if gender == "male" else 0
    estimate = 1.20 * bmi_value + 0.23 * age - 10.8 * sex - 5.4
    return round(max(estimate, 3.0), 1)


def bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + (5 if gender == "male" else -161), 0)


def tdee(bmr_value: float, activity_level: str) -> float:
    return round(bmr_value * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2), 0)


def daily_calorie_target(tdee_value: float, goal: str) -> float:
    adjustment = GOAL_CALORIE_ADJUSTMENT.get(goal, 0.0)
    return round(tdee_value * (1 + adjustment), 0)


def macros(daily_calories: float, weight_kg: float, goal: str) -> dict:
    protein_per_kg = 2.0 if goal == "build_muscle" else (1.8 if goal == "lose_weight" else 1.6)
    protein_g = round(protein_per_kg * weight_kg, 0)
    fat_pct = 0.30 if goal != "build_muscle" else 0.25
    fat_g = round((daily_calories * fat_pct) / 9, 0)
    remaining_calories = daily_calories - (protein_g * 4) - (fat_g * 9)
    carbs_g = round(max(remaining_calories, 0) / 4, 0)
    return {"protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g}


def water_target_ml(weight_kg: float, activity_level: str) -> float:
    base = weight_kg * 35
    bonus = {"sedentary": 0, "light": 250, "moderate": 500, "active": 750, "very_active": 1000}
    return round(base + bonus.get(activity_level, 0), -1)


def body_type(bmi_value: float, body_fat_pct: float) -> str:
    if bmi_value < 20 and body_fat_pct < 15:
        return "ectomorph"
    if bmi_value > 27 or body_fat_pct > 28:
        return "endomorph"
    return "mesomorph"


def fitness_level(activity_level: str, experience_level: str = "beginner") -> str:
    score = {"sedentary": 0, "light": 1, "moderate": 2, "active": 3, "very_active": 4}.get(activity_level, 0)
    score += {"beginner": 0, "intermediate": 1, "advanced": 2}.get(experience_level, 0)
    if score <= 1:
        return "beginner"
    if score <= 4:
        return "intermediate"
    return "advanced"


def metabolic_score(bmi_value: float, activity_level: str, sleep_hours: float = 7.0, body_fat_pct: float = 20.0) -> int:
    """0-100 composite wellness score — a friendly single number, not a medical diagnostic."""
    score = 100
    if bmi_value < 18.5 or bmi_value > 27:
        score -= 15
    elif bmi_value > 24.9:
        score -= 7
    activity_bonus = {"sedentary": -15, "light": -5, "moderate": 5, "active": 12, "very_active": 15}
    score += activity_bonus.get(activity_level, 0)
    if sleep_hours < 6:
        score -= 10
    elif sleep_hours >= 7.5:
        score += 5
    if body_fat_pct > 30:
        score -= 10
    elif body_fat_pct < 12:
        score -= 3
    return int(max(0, min(100, score)))


def full_body_analysis(profile: dict) -> dict:
    """profile: height_cm, weight_kg, age, gender, activity_level, fitness_goal,
    body_fat_pct(optional), experience_level(optional), sleep_hours(optional)."""
    weight = profile["weight_kg"]
    height = profile["height_cm"]
    age = profile["age"]
    gender = profile["gender"]
    activity = profile["activity_level"]
    goal = profile["fitness_goal"]

    bmi_v = bmi(weight, height)
    bf = body_fat_estimate(bmi_v, age, gender, profile.get("body_fat_pct"))
    bmr_v = bmr(weight, height, age, gender)
    tdee_v = tdee(bmr_v, activity)
    calories = daily_calorie_target(tdee_v, goal)
    macro = macros(calories, weight, goal)
    water = water_target_ml(weight, activity)
    hw_min, hw_max = healthy_weight_range(height)
    btype = body_type(bmi_v, bf)
    flevel = fitness_level(activity, profile.get("experience_level", "beginner"))
    mscore = metabolic_score(bmi_v, activity, profile.get("sleep_hours", 7.0), bf)

    recommendations = _recommendations(bmi_v, bf, activity, goal, mscore)

    return {
        "bmi": bmi_v,
        "healthy_weight_min": hw_min,
        "healthy_weight_max": hw_max,
        "body_fat_estimate": bf,
        "bmr": bmr_v,
        "tdee": tdee_v,
        "daily_calories": calories,
        "protein_g": macro["protein_g"],
        "carbs_g": macro["carbs_g"],
        "fat_g": macro["fat_g"],
        "water_target_ml": water,
        "body_type": btype,
        "fitness_level": flevel,
        "metabolic_score": mscore,
        "recommendations": recommendations,
    }


def _recommendations(bmi_v, bf, activity, goal, mscore) -> list[str]:
    recs = []
    if bmi_v > 24.9:
        recs.append("A moderate calorie deficit combined with strength training will protect muscle while you lose fat.")
    elif bmi_v < 18.5:
        recs.append("Focus on a calorie surplus with protein-rich meals to build healthy mass.")
    else:
        recs.append("Your weight is in a healthy range — focus on performance and body composition goals.")
    if activity in ("sedentary", "light"):
        recs.append("Aim to add 1-2 more active days per week — even brisk walking counts.")
    if bf > 25:
        recs.append("Prioritize resistance training 3x/week to improve body composition over time.")
    if goal == "build_muscle":
        recs.append("Hit your protein target daily and progressively overload your main lifts.")
    if mscore < 60:
        recs.append("Small, consistent habits (sleep, hydration, daily movement) will move your score fastest.")
    recs.append("Stay consistent — the AI plan adapts as you log more progress.")
    return recs
