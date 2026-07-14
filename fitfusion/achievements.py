"""Achievement rules — simple, transparent milestones evaluated against logged data."""
from fitfusion import db

ACHIEVEMENTS = {
    "first_workout": ("🏋️", "First Workout Logged"),
    "first_meal": ("🥗", "First Meal Logged"),
    "streak_3": ("🔥", "3-Day Streak"),
    "streak_7": ("🔥🔥", "7-Day Streak"),
    "streak_30": ("🔥🔥🔥", "30-Day Streak"),
    "weight_tracker": ("⚖️", "Logged Weight 5 Times"),
    "metabolic_master": ("🥇", "Metabolic Score 80+"),
    "hydration_hero": ("💧", "Hit Water Goal"),
}


def evaluate_and_unlock(user_id: int) -> list[dict]:
    workouts = db.workout_logs(user_id)
    meals = db.all_meals(user_id)
    streak = db.workout_streak(user_id)
    weights = db.weight_logs(user_id)
    analysis = db.latest_body_analysis(user_id)
    water = db.water_today(user_id)

    checks = {
        "first_workout": len(workouts) >= 1,
        "first_meal": len(meals) >= 1,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "streak_30": streak >= 30,
        "weight_tracker": len(weights) >= 5,
        "metabolic_master": bool(analysis and analysis["metabolic_score"] >= 80),
        "hydration_hero": water >= 8,
    }
    for key, passed in checks.items():
        if passed:
            db.unlock_achievement(user_id, key)

    return [
        {"key": row["key"], "icon": ACHIEVEMENTS.get(row["key"], ("🏆", row["key"]))[0],
         "title": ACHIEVEMENTS.get(row["key"], ("🏆", row["key"]))[1], "unlocked_at": row["unlocked_at"]}
        for row in db.achievements(user_id)
    ]
