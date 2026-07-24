import json

import streamlit as st

from fitfusion.i18n import t
from fitfusion.nav import require_login
from fitfusion.styles import section_title, stat_card, glass_card
from fitfusion import db, videos
from fitfusion.workout_engine import EXERCISES

st.set_page_config(page_title=f"{t('trainer_title')} · FitFusion", page_icon="🕺", layout="centered")
user = require_login()

st.title(f"🕺 {t('trainer_title')}")


def cal_per_min_for(exercise_id: str) -> float:
    entry = next((e for e in EXERCISES if e["id"] == exercise_id), None)
    return entry["cal_per_min"] if entry else 8


def render_demo(exercise_id: str, exercise_name: str):
    section_title("🎬", t("watch_demo"))
    video_url = videos.EXERCISE_VIDEOS.get(exercise_id)
    if video_url:
        st.video(video_url)
    else:
        st.link_button(f"▶️ {t('watch_demo')}", videos.get_demo_video_url(exercise_id, exercise_name), use_container_width=True)
        st.caption(t("demo_not_ready"))


def render_tracking(cal_per_min: float, key_prefix: str):
    """Renders the manual rep/duration tracking UI. Returns (reps, duration_min, accuracy)
    ready to be logged by the caller."""
    st.markdown(f"**{t('manual_rep_counter')}**")
    reps_key = f"{key_prefix}_manual_reps"
    if reps_key not in st.session_state:
        st.session_state[reps_key] = 0
    mc1, mc2, mc3 = st.columns(3)
    if mc1.button("➖", use_container_width=True, key=f"{key_prefix}_minus"):
        st.session_state[reps_key] = max(0, st.session_state[reps_key] - 1)
    mc2.markdown(f"<h2 style='text-align:center'>{st.session_state[reps_key]}</h2>", unsafe_allow_html=True)
    if mc3.button("➕", use_container_width=True, key=f"{key_prefix}_plus"):
        st.session_state[reps_key] += 1
    duration = st.slider(t("duration") + " (min)", 1, 60, 5, key=f"{key_prefix}_duration")
    stat_card("🔥", t("calories_burned"), f"{round(duration * cal_per_min, 1)} {t('kcal')}")
    return st.session_state[reps_key], duration, None


# --------------------------------------------------------------------------------------
plan_row = db.latest_workout_plan(user["id"])
plan = json.loads(plan_row["plan_json"]) if plan_row else None

if plan and plan["days"]:
    day_labels = [f"{d['day']} · {d['focus']}" for d in plan["days"]]
    if "trainer_day_idx" not in st.session_state:
        st.session_state["trainer_day_idx"] = 0
    if "trainer_queue" not in st.session_state:
        st.session_state["trainer_queue"] = plan["days"][st.session_state["trainer_day_idx"]]["exercises"]
        st.session_state["trainer_idx"] = 0

    section_title("📅", t("todays_routine"))
    chosen_day = st.selectbox(
        t("choose_day"), range(len(day_labels)), index=st.session_state["trainer_day_idx"],
        format_func=lambda i: day_labels[i],
    )
    if chosen_day != st.session_state["trainer_day_idx"]:
        st.session_state["trainer_day_idx"] = chosen_day
        st.session_state["trainer_queue"] = plan["days"][chosen_day]["exercises"]
        st.session_state["trainer_idx"] = 0
        st.rerun()

    queue = st.session_state["trainer_queue"]
    idx = st.session_state.get("trainer_idx", 0)

    strip = " &nbsp; ".join(
        f"{'✅' if i < idx else ('▶️' if i == idx else '⬜')} {ex['name']}" for i, ex in enumerate(queue)
    )
    st.markdown(f"<p style='color:#B3B3B3'>{strip}</p>", unsafe_allow_html=True)

    if idx >= len(queue):
        completed = sum(1 for e in queue if e.get("completed"))
        total = len(queue)
        pct = round(completed / total * 100) if total else 0

        if pct >= 100:
            st.balloons()
            icon, glow = "🎉", "gold"
            title, body = t("workout_complete_title"), t("workout_complete_body")
        elif pct >= 75:
            icon, glow = "💪", "gold"
            title, body = t("workout_partial_title", pct=pct), t("workout_partial_body_high")
        elif pct >= 40:
            icon, glow = "🙂", "blue"
            title, body = t("workout_partial_title", pct=pct), t("workout_partial_body_mid")
        else:
            icon, glow = "🌱", ""
            title, body = t("workout_partial_title", pct=pct), t("workout_partial_body_low")

        glass_card(
            f"<div style='text-align:center'><div style='font-size:44px'>{icon}</div>"
            f"<h2>{title}</h2><p>{body}</p></div>",
            glow=glow,
        )
        total_calories = sum(e.get("est_calories", 0) for e in queue)
        c1, c2 = st.columns(2)
        with c1:
            stat_card("💪", t("exercises_completed"), f"{completed}/{total}")
        with c2:
            stat_card("🔥", t("calories_burned"), f"{total_calories} {t('kcal')}")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button(f"🔁 {t('do_another_day')}", use_container_width=True):
                st.session_state["trainer_idx"] = 0
                st.rerun()
        with cc2:
            st.page_link("pages/6_📈_Progress.py", label=t("progress_title"), icon="📈")
    else:
        exercise = queue[idx]
        st.progress(idx / len(queue), text=t("exercise_progress", current=idx + 1, total=len(queue)))

        section_title("🎯", exercise["name"])
        st.caption(f"{t('sets')}: {exercise['sets']} · {t('reps')}: {exercise['reps']} · {t('rest')}: {exercise['rest_sec']}s")
        st.write(", ".join(m.replace("_", " ").title() for m in exercise["muscles"]))

        render_demo(exercise["id"], exercise["name"])

        st.divider()
        cal_per_min = cal_per_min_for(exercise["id"])
        reps, duration, accuracy = render_tracking(cal_per_min, f"routine_{idx}")

        st.divider()
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button(f"⏭ {t('skip_exercise')}", use_container_width=True):
                queue[idx]["est_calories"] = 0
                queue[idx]["completed"] = False
                st.session_state["trainer_idx"] = idx + 1
                st.rerun()
        with bc2:
            if st.button(f"✅ {t('mark_done_next')}", use_container_width=True, type="primary"):
                actual_calories = round(duration * cal_per_min, 1) if reps > 0 else 0
                db.log_workout(
                    user["id"], exercise["name"], sets=exercise.get("sets", 1), reps=reps,
                    duration_min=duration, calories_burned=actual_calories, accuracy_score=accuracy,
                )
                queue[idx]["est_calories"] = actual_calories
                queue[idx]["completed"] = reps > 0
                st.session_state["trainer_idx"] = idx + 1
                st.success(t("success_saved"))
                st.rerun()

else:
    st.info(t("no_plan_yet"))
    st.page_link("pages/2_🏋️_Workouts.py", label=t("go_to_workouts"), icon="🏋️")
    st.divider()

    section_title("🎯", t("free_practice"))
    exercise = st.selectbox(t("select_exercise"), EXERCISES, format_func=lambda e: e["name"])

    st.write(", ".join(m.replace("_", " ").title() for m in exercise["muscles"]))
    st.caption(f"{t('difficulty')}: {exercise['difficulty'].title()}")
    render_demo(exercise["id"], exercise["name"])

    st.divider()
    reps, duration, accuracy = render_tracking(exercise["cal_per_min"], "free")

    if st.button(f"✅ {t('start_workout')}", use_container_width=True, type="primary"):
        db.log_workout(
            user["id"], exercise["name"], sets=1, reps=reps,
            duration_min=duration, calories_burned=round(duration * exercise["cal_per_min"], 1), accuracy_score=accuracy,
        )
        st.success(t("success_saved"))
        st.balloons()
