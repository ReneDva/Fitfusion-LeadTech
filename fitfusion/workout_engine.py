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


def build_exercise(ex_id: str, sets: int, rest_sec: int, reps: str = None) -> dict:
    """Builds a display/session exercise dict (with calorie estimate) from a catalog id.
    Shared by plan generation and session-only adaptation so calorie math stays consistent."""
    ex = next((e for e in EXERCISES if e["id"] == ex_id), None)
    if not ex:
        return None
    if ex.get("time_based"):
        reps_display = "30-45 sec"
        est_minutes = sets * 0.75
    else:
        reps_display = reps or "10-12"
        avg_reps = 12
        est_minutes = sets * (avg_reps * 3 / 60 + rest_sec / 60)
    calories = round(est_minutes * ex["cal_per_min"])
    return {
        "id": ex["id"],
        "name": ex["name"],
        "sets": sets,
        "reps": reps_display,
        "rest_sec": rest_sec,
        "muscles": ex["muscles"],
        "difficulty": ex["difficulty"],
        "est_calories": calories,
        "trackable": ex.get("trackable", False),
    }


_AVOID_FOR_BACK_PAIN = {"deadlift", "barbell_squat", "kettlebell_swing", "burpee", "russian_twist", "mountain_climber"}
_EQUIPMENT_KEYWORDS = ["dumbbells", "barbell", "bench", "resistance_band", "pull_up_bar", "machine", "kettlebell", "jump_rope", "bike"]
_BACK_PAIN_TERMS = ["back pain", "back hurt", "hurt my back", "lower back", "sore back", "back injury", "my back"]
_TIME_TERMS = ["less time", "short on time", "shorter", "in a hurry", "no time", "quick workout", "running late"]


def adapt_day_offline(day_exercises: list[dict], request: str, equipment: list[str], location: str) -> tuple[list[dict], str]:
    """Rule-based, session-only workout adaptation used when no Gemini key is configured
    (or the AI call fails). Swaps out unsafe/unavailable exercises and trims for time —
    never touches the saved weekly plan."""
    request_l = (request or "").lower()
    pool = _filter_exercises(equipment, location)
    missing_equipment = {kw for kw in _EQUIPMENT_KEYWORDS if kw in request_l or kw.replace("_", " ") in request_l}
    avoid_back = any(term in request_l for term in _BACK_PAIN_TERMS)
    want_shorter = any(term in request_l for term in _TIME_TERMS)

    notes = []
    used_ids = set()
    new_exercises = []
    for ex in day_exercises:
        source = next((e for e in EXERCISES if e["id"] == ex["id"]), None)
        needs_swap = source is not None and (
            (avoid_back and source["id"] in _AVOID_FOR_BACK_PAIN)
            or (missing_equipment and set(source["equipment"]) & missing_equipment)
        )
        if needs_swap:
            candidates = [
                c for c in pool
                if c["category"] == source["category"] and c["id"] not in used_ids
                and c["id"] not in _AVOID_FOR_BACK_PAIN
                and not (set(c["equipment"]) & missing_equipment)
            ]
            if candidates:
                replacement = candidates[0]
                used_ids.add(replacement["id"])
                new_exercises.append(build_exercise(replacement["id"], ex["sets"], ex["rest_sec"], ex["reps"]))
                notes.append(f"Swapped {source['name']} for {replacement['name']}")
            else:
                notes.append(f"Dropped {source['name']} (no safe alternative on hand)")
            continue
        used_ids.add(ex["id"])
        new_exercises.append(dict(ex))

    if want_shorter and new_exercises:
        keep_n = max(2, round(len(new_exercises) * 0.7))
        new_exercises = [
            build_exercise(e["id"], max(2, e["sets"] - 1), max(20, e["rest_sec"] - 15), e["reps"])
            for e in new_exercises[:keep_n]
        ]
        notes.append(f"Trimmed to {len(new_exercises)} exercises with fewer sets and shorter rest to save time")

    if not new_exercises:
        new_exercises = day_exercises
        notes = ["Couldn't find a safe adaptation — showing your original session"]
    if not notes:
        notes = ["No changes needed, this session already fits your request"]

    return new_exercises, ". ".join(notes) + "."


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
            built = build_exercise(ex["id"], scheme["sets"], scheme["rest_sec"], scheme["reps"])
            day_calories += built["est_calories"]
            day_exercises.append(built)
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
