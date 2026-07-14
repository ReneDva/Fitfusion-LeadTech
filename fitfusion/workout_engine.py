"""Rule-based AI workout plan generator.

Deterministic and fully offline (no LLM call needed to produce a safe, structured plan) —
this is what "the AI" builds instantly. The optional AI Coach can add written commentary
on top via fitfusion.ai, but the plan itself never depends on network access.
"""
import json
import random

from fitfusion.config import DATA_DIR

with open(DATA_DIR / "exercises.json", "r", encoding="utf-8") as f:
    EXERCISES = json.load(f)

SPLITS = {
    1: ["full_body"],
    2: ["full_body", "full_body"],
    3: ["full_body", "full_body", "full_body"],
    4: ["upper", "lower", "upper", "lower"],
    5: ["push", "pull", "legs", "upper", "cardio"],
    6: ["push", "pull", "legs", "push", "pull", "legs"],
    7: ["push", "pull", "legs", "upper", "lower", "cardio", "full_body"],
}

FOCUS_CATEGORIES = {
    "full_body": ["legs", "push", "pull", "core"],
    "upper": ["push", "pull", "core"],
    "lower": ["legs", "core"],
    "push": ["push", "core"],
    "pull": ["pull", "core"],
    "legs": ["legs", "core"],
    "cardio": ["cardio", "full_body"],
}

GOAL_SCHEME = {
    "lose_weight": {"sets": 3, "reps": "12-15", "rest_sec": 40},
    "build_muscle": {"sets": 4, "reps": "8-12", "rest_sec": 75},
    "maintain": {"sets": 3, "reps": "10-12", "rest_sec": 60},
    "improve_endurance": {"sets": 3, "reps": "15-20", "rest_sec": 30},
    "general_health": {"sets": 3, "reps": "10-12", "rest_sec": 60},
}

EXPERIENCE_EXERCISE_COUNT = {"beginner": 3, "intermediate": 4, "advanced": 5}


def performance_adjustment(user_id: int) -> float:
    """AI 'continuous adaptation': bump volume for consistent, accurate users; ease off otherwise."""
    from fitfusion.db import workout_logs, workout_streak

    logs = workout_logs(user_id)
    if not logs:
        return 1.0
    streak = workout_streak(user_id)
    accuracies = [row["accuracy_score"] for row in logs if row["accuracy_score"] is not None]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 80
    factor = 1.0
    if streak >= 7:
        factor += 0.15
    elif streak >= 3:
        factor += 0.07
    if avg_accuracy < 65:
        factor -= 0.1
    elif avg_accuracy > 90:
        factor += 0.05
    return round(max(0.7, min(1.3, factor)), 2)


def _filter_exercises(equipment: list[str], location: str):
    equipment_set = set(equipment) | {"none"}
    return [
        ex for ex in EXERCISES
        if location in ex["locations"] and set(ex["equipment"]).issubset(equipment_set)
    ]


def generate_plan(profile: dict, user_id: int = None) -> dict:
    """profile: fitness_goal, experience_level, workout_location, equipment(list),
    workout_days_per_week, session_minutes."""
    goal = profile.get("fitness_goal", "general_health")
    experience = profile.get("experience_level", "beginner")
    location = profile.get("workout_location", "home")
    equipment = profile.get("equipment", [])
    days = int(profile.get("workout_days_per_week", 3) or 3)
    days = max(1, min(days, 7))
    session_minutes = int(profile.get("session_minutes", 30) or 30)

    pool = _filter_exercises(equipment, location)
    scheme = dict(GOAL_SCHEME.get(goal, GOAL_SCHEME["general_health"]))
    n_exercises = EXPERIENCE_EXERCISE_COUNT.get(experience, 3)

    factor = performance_adjustment(user_id) if user_id else 1.0
    scheme["sets"] = max(2, round(scheme["sets"] * factor))

    split = SPLITS[days]
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    plan_days = []
    total_calories = 0
    for i, focus in enumerate(split):
        categories = FOCUS_CATEGORIES.get(focus, ["full_body"])
        candidates = [ex for ex in pool if ex["category"] in categories]
        if not candidates:
            candidates = pool
        random.Random(f"{focus}-{i}-{goal}").shuffle(candidates)
        chosen = candidates[:n_exercises] if candidates else []

        day_exercises = []
        day_calories = 0
        for ex in chosen:
            sets = scheme["sets"]
            if ex.get("time_based"):
                reps_display = "30-45 sec"
                est_minutes = sets * 0.75
            else:
                reps_display = scheme["reps"]
                avg_reps = 12
                est_minutes = sets * (avg_reps * 3 / 60 + scheme["rest_sec"] / 60)
            calories = round(est_minutes * ex["cal_per_min"])
            day_calories += calories
            day_exercises.append({
                "id": ex["id"],
                "name": ex["name"],
                "sets": sets,
                "reps": reps_display,
                "rest_sec": scheme["rest_sec"],
                "muscles": ex["muscles"],
                "difficulty": ex["difficulty"],
                "est_calories": calories,
                "trackable": ex.get("trackable", False),
            })
        total_calories += day_calories
        plan_days.append({
            "day": day_names[i % 7],
            "focus": focus.replace("_", " ").title(),
            "exercises": day_exercises,
            "duration_min": min(session_minutes, max(15, sum(1 for _ in day_exercises) * 8)),
            "est_calories": day_calories,
        })

    return {
        "goal": goal,
        "experience_level": experience,
        "days_per_week": days,
        "adjustment_factor": factor,
        "days": plan_days,
        "weekly_est_calories": total_calories,
    }
