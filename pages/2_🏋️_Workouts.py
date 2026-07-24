import json

import streamlit as st

from fitfusion.config import WORKOUT_LOCATIONS, EXPERIENCE_LEVELS
from fitfusion.i18n import t, current_language
from fitfusion.nav import require_login
from fitfusion.styles import section_title, glass_card, empty_state
from fitfusion import db, workout_engine, ai

st.set_page_config(page_title=f"{t('workout_plan_title')} · FitFusion", page_icon="🏋️", layout="centered")
user = require_login()
profile = db.get_profile(user["id"])

st.title(f"🏋️ {t('workout_plan_title')}")

with st.expander(f"⚙️ {t('equipment')} / {t('workout_location')} / {t('workout_days_per_week')}"):
    location = st.selectbox(t("workout_location"), WORKOUT_LOCATIONS,
                             index=WORKOUT_LOCATIONS.index(profile["workout_location"] or "home"),
                             format_func=lambda l: t(f"location_{l}"))
    equipment = st.multiselect(
        t("equipment"),
        ["dumbbells", "barbell", "bench", "resistance_band", "pull_up_bar", "machine", "kettlebell", "jump_rope", "bike"],
        default=json.loads(profile["equipment"] or "[]"),
        format_func=lambda e: t(f"equip_{e}"),
        placeholder=t("choose_options"),
    )
    experience = st.selectbox(t("experience_level"), EXPERIENCE_LEVELS,
                               index=EXPERIENCE_LEVELS.index(profile["experience_level"] or "beginner"),
                               format_func=lambda e: t(f"experience_{e}"))
    c1, c2 = st.columns(2)
    days = c1.slider(t("workout_days_per_week"), 1, 7, int(profile["workout_days_per_week"] or 3))
    minutes = c2.slider(t("session_minutes"), 15, 90, int(profile["session_minutes"] or 30))

    if st.button(t("regenerate_plan"), type="primary", width='stretch'):
        db.update_profile(
            user["id"], workout_location=location, equipment=json.dumps(equipment),
            experience_level=experience, workout_days_per_week=days, session_minutes=minutes,
        )
        plan_input = dict(
            fitness_goal=profile["fitness_goal"], experience_level=experience,
            workout_location=location, equipment=equipment,
            workout_days_per_week=days, session_minutes=minutes,
        )
        plan = workout_engine.generate_plan(plan_input, user["id"])
        db.save_workout_plan(user["id"], profile["fitness_goal"], plan)
        st.success(t("success_saved"))
        st.rerun()

if "adapt_dialog_day" not in st.session_state:
    st.session_state["adapt_dialog_day"] = None


@st.dialog(t("adapt_workout"))
def adapt_workout_dialog(day_idx: int, day: dict):
    result_key = f"adapted_day_{day_idx}"
    st.caption(t("adapt_workout_hint"))
    request = st.text_area(t("adapt_workout_placeholder"), key=f"adapt_request_{day_idx}", height=90)

    if st.button(t("adapt_workout_submit"), type="primary", width='stretch', disabled=not request.strip()):
        with st.spinner(t("ai_thinking")):
            st.session_state[result_key] = ai.adapt_workout(day["exercises"], request, current_language(), equipment, location)
        st.rerun()

    adapted = st.session_state.get(result_key)
    if adapted:
        if adapted["note"]:
            st.success(adapted["note"])
        for ex in adapted["exercises"]:
            st.markdown(f"- **{ex['name']}** — {t('sets')}: {ex['sets']} × {ex['reps']}, {t('rest')}: {ex['rest_sec']}s")

        c1, c2 = st.columns(2)
        if c1.button(f"▶️ {t('start_adapted_workout')}", type="primary", width='stretch'):
            st.session_state["trainer_queue"] = adapted["exercises"]
            st.session_state["trainer_idx"] = 0
            st.session_state["trainer_day_idx"] = day_idx
            del st.session_state[result_key]
            st.session_state["adapt_dialog_day"] = None
            st.switch_page("pages/3_⏱️_Workout_Tracker.py")
        if c2.button(t("cancel"), width='stretch'):
            del st.session_state[result_key]
            st.session_state["adapt_dialog_day"] = None
            st.rerun()


plan_row = db.latest_workout_plan(user["id"])
if not plan_row:
    empty_state(t("empty_no_data"))
    st.stop()

plan = json.loads(plan_row["plan_json"])
st.caption(f"AI-adapted volume: ×{plan.get('adjustment_factor', 1.0)} · {t('est_calories_burned')}: {plan.get('weekly_est_calories', 0)} {t('kcal')}/week")

day_tabs = st.tabs([d["day"] for d in plan["days"]])
for day_idx, (tab, day) in enumerate(zip(day_tabs, plan["days"])):
    with tab:
        section_title("📅", f"{day['focus']} · {day['duration_min']} min · {day['est_calories']} {t('kcal')}")
        for ex in day["exercises"]:
            muscles = ", ".join(ex["muscles"])
            glass_card(
                f"""
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <b style='font-size:16px'>{ex['name']}</b>
                </div>
                <p style='color:#B3B3B3;margin:6px 0'>{t('target_muscles')}: {muscles} · {t('difficulty')}: {ex['difficulty'].title()}</p>
                <p style='margin:0'>
                    <b>{t('sets')}:</b> {ex['sets']} &nbsp; <b>{t('reps')}:</b> {ex['reps']} &nbsp;
                    <b>{t('rest')}:</b> {ex['rest_sec']}s &nbsp; <b>{t('est_calories_burned')}:</b> {ex['est_calories']} {t('kcal')}
                </p>
                """
            )
        btn_col1, btn_col2 = st.columns(2)
        if btn_col1.button(f"▶️ {t('start_workout')}", key=f"start_{day['day']}", width='stretch', type="primary"):
            st.session_state["trainer_queue"] = day["exercises"]
            st.session_state["trainer_idx"] = 0
            st.session_state["trainer_day_idx"] = day_idx
            st.switch_page("pages/3_⏱️_Workout_Tracker.py")
        if btn_col2.button(f"💬 {t('adapt_workout')}", key=f"adapt_{day['day']}", width='stretch'):
            st.session_state["adapt_dialog_day"] = day_idx
            st.rerun()

open_day_idx = st.session_state.get("adapt_dialog_day")
if open_day_idx is not None:
    adapt_workout_dialog(open_day_idx, plan["days"][open_day_idx])
