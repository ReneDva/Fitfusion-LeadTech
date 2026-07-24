"""SQLite persistence layer. Zero external services — one file on disk."""
import sqlite3
import json
import datetime as dt
from contextlib import contextmanager

import streamlit as st

from fitfusion.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    height_cm REAL, weight_kg REAL, age INTEGER, gender TEXT,
    activity_level TEXT, fitness_goal TEXT,
    body_fat_pct REAL, muscle_mass_kg REAL,
    dietary_preference TEXT, food_allergies TEXT, medical_limitations TEXT,
    experience_level TEXT DEFAULT 'beginner',
    workout_location TEXT DEFAULT 'home',
    equipment TEXT DEFAULT '[]',
    workout_days_per_week INTEGER DEFAULT 3,
    session_minutes INTEGER DEFAULT 30,
    onboarded INTEGER DEFAULT 0,
    language TEXT DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS body_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    bmi REAL, healthy_weight_min REAL, healthy_weight_max REAL,
    body_fat_estimate REAL, bmr REAL, tdee REAL, daily_calories REAL,
    protein_g REAL, carbs_g REAL, fat_g REAL, water_target_ml REAL,
    body_type TEXT, fitness_level TEXT, metabolic_score INTEGER,
    recommendations_json TEXT
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    goal TEXT,
    plan_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    exercise TEXT, sets INTEGER, reps INTEGER,
    duration_min REAL, calories_burned REAL, accuracy_score REAL
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    name TEXT, calories REAL, protein REAL, carbs REAL, fat REAL,
    fiber REAL, sugar REAL, sodium REAL, quality_score INTEGER,
    source TEXT
);

CREATE TABLE IF NOT EXISTS water_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, date TEXT NOT NULL, cups INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sleep_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, date TEXT NOT NULL, hours REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS weight_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, date TEXT NOT NULL, weight_kg REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, key TEXT NOT NULL, unlocked_at TEXT NOT NULL,
    UNIQUE(user_id, key)
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    plan TEXT DEFAULT 'free', status TEXT DEFAULT 'active', started_at TEXT
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Adds columns introduced after a user's DB file was first created.
    CREATE TABLE IF NOT EXISTS in SCHEMA only affects brand-new databases."""
    try:
        conn.execute("ALTER TABLE profiles ADD COLUMN language TEXT DEFAULT 'en'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists


@st.cache_resource
def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    _migrate(conn)
    return conn


@contextmanager
def get_cursor():
    conn = _connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def today() -> str:
    return dt.date.today().isoformat()


# ---- users / profile -------------------------------------------------
def create_user(email, username, name, password_hash) -> int:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, username, name, password_hash, created_at) VALUES (?,?,?,?,?)",
            (email.lower(), username.lower(), name, password_hash, now()),
        )
        user_id = cur.lastrowid
        cur.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
        cur.execute(
            "INSERT INTO subscriptions (user_id, plan, status, started_at) VALUES (?, 'free','active',?)",
            (user_id, now()),
        )
        return user_id


def find_user_by_login(identifier: str):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE email = ? OR username = ?",
            (identifier.lower(), identifier.lower()),
        )
        return cur.fetchone()


def get_user(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()


def get_profile(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        return cur.fetchone()


def update_profile(user_id: int, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    with get_cursor() as cur:
        cur.execute(f"UPDATE profiles SET {cols} WHERE user_id = ?", (*fields.values(), user_id))


def get_subscription(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
        return cur.fetchone()


def set_subscription(user_id: int, plan: str):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE subscriptions SET plan = ?, status='active', started_at = ? WHERE user_id = ?",
            (plan, now(), user_id),
        )


# ---- body analysis ------------------------------------------------------
def save_body_analysis(user_id: int, result: dict) -> int:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO body_analyses
            (user_id, created_at, bmi, healthy_weight_min, healthy_weight_max, body_fat_estimate,
             bmr, tdee, daily_calories, protein_g, carbs_g, fat_g, water_target_ml,
             body_type, fitness_level, metabolic_score, recommendations_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id, now(), result["bmi"], result["healthy_weight_min"], result["healthy_weight_max"],
                result["body_fat_estimate"], result["bmr"], result["tdee"], result["daily_calories"],
                result["protein_g"], result["carbs_g"], result["fat_g"], result["water_target_ml"],
                result["body_type"], result["fitness_level"], result["metabolic_score"],
                json.dumps(result.get("recommendations", [])),
            ),
        )
        return cur.lastrowid


def latest_body_analysis(user_id: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM body_analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)
        )
        return cur.fetchone()


def all_body_analyses(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM body_analyses WHERE user_id = ? ORDER BY created_at ASC", (user_id,))
        return cur.fetchall()


# ---- workout plans / logs ------------------------------------------------
def save_workout_plan(user_id: int, goal: str, plan: dict) -> int:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO workout_plans (user_id, created_at, goal, plan_json) VALUES (?,?,?,?)",
            (user_id, now(), goal, json.dumps(plan)),
        )
        return cur.lastrowid


def latest_workout_plan(user_id: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM workout_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)
        )
        return cur.fetchone()


def log_workout(user_id: int, exercise: str, sets: int, reps: int, duration_min: float,
                 calories_burned: float, accuracy_score: float = None):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO workout_logs (user_id, date, exercise, sets, reps, duration_min,
               calories_burned, accuracy_score) VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, today(), exercise, sets, reps, duration_min, calories_burned, accuracy_score),
        )


def workout_logs(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM workout_logs WHERE user_id = ? ORDER BY date ASC", (user_id,))
        return cur.fetchall()


# ---- nutrition ------------------------------------------------------------
def log_meal(user_id: int, meal: dict):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO meals (user_id, date, name, calories, protein, carbs, fat, fiber, sugar,
               sodium, quality_score, source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id, today(), meal.get("name", "Meal"), meal.get("calories", 0), meal.get("protein", 0),
                meal.get("carbs", 0), meal.get("fat", 0), meal.get("fiber", 0), meal.get("sugar", 0),
                meal.get("sodium", 0), meal.get("quality_score", 70), meal.get("source", "manual"),
            ),
        )


def meals_for_date(user_id: int, date: str = None):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM meals WHERE user_id = ? AND date = ? ORDER BY id ASC", (user_id, date or today())
        )
        return cur.fetchall()


def all_meals(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM meals WHERE user_id = ? ORDER BY date ASC", (user_id,))
        return cur.fetchall()


# ---- water / sleep / weight ------------------------------------------------
def log_water(user_id: int, cups: int):
    with get_cursor() as cur:
        cur.execute("SELECT id, cups FROM water_logs WHERE user_id=? AND date=?", (user_id, today()))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE water_logs SET cups = ? WHERE id = ?", (row["cups"] + cups, row["id"]))
        else:
            cur.execute("INSERT INTO water_logs (user_id, date, cups) VALUES (?,?,?)", (user_id, today(), cups))


def water_today(user_id: int) -> int:
    with get_cursor() as cur:
        cur.execute("SELECT cups FROM water_logs WHERE user_id=? AND date=?", (user_id, today()))
        row = cur.fetchone()
        return row["cups"] if row else 0


def log_sleep(user_id: int, hours: float):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM sleep_logs WHERE user_id=? AND date=?", (user_id, today()))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE sleep_logs SET hours = ? WHERE id = ?", (hours, row["id"]))
        else:
            cur.execute("INSERT INTO sleep_logs (user_id, date, hours) VALUES (?,?,?)", (user_id, today(), hours))


def sleep_logs(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sleep_logs WHERE user_id=? ORDER BY date ASC", (user_id,))
        return cur.fetchall()


def log_weight(user_id: int, weight_kg: float):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM weight_logs WHERE user_id=? AND date=?", (user_id, today()))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE weight_logs SET weight_kg = ? WHERE id = ?", (weight_kg, row["id"]))
        else:
            cur.execute(
                "INSERT INTO weight_logs (user_id, date, weight_kg) VALUES (?,?,?)", (user_id, today(), weight_kg)
            )
    update_profile(user_id, weight_kg=weight_kg)


def weight_logs(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM weight_logs WHERE user_id=? ORDER BY date ASC", (user_id,))
        return cur.fetchall()


# ---- achievements -----------------------------------------------------
def unlock_achievement(user_id: int, key: str) -> bool:
    with get_cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO achievements (user_id, key, unlocked_at) VALUES (?,?,?)", (user_id, key, now())
            )
            return True
        except sqlite3.IntegrityError:
            return False


def achievements(user_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM achievements WHERE user_id=? ORDER BY unlocked_at ASC", (user_id,))
        return cur.fetchall()


def workout_streak(user_id: int) -> int:
    logs = workout_logs(user_id)
    dates = sorted({row["date"] for row in logs}, reverse=True)
    if not dates:
        return 0
    streak = 0
    cursor_date = dt.date.today()
    for d in dates:
        d_date = dt.date.fromisoformat(d)
        if d_date == cursor_date or d_date == cursor_date - dt.timedelta(days=1):
            streak += 1
            cursor_date = d_date
        else:
            break
    return streak


# ---- AI conversations -----------------------------------------------------
def save_message(user_id: int, role: str, content: str):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO ai_conversations (user_id, role, content, created_at) VALUES (?,?,?,?)",
            (user_id, role, content, now()),
        )


def conversation_history(user_id: int, limit: int = 30):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM ai_conversations WHERE user_id=? ORDER BY id ASC LIMIT ?", (user_id, limit)
        )
        return cur.fetchall()
