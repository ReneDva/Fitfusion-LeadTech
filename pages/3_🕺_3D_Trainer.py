import time

import streamlit as st

from fitfusion.i18n import t
from fitfusion.nav import require_login
from fitfusion.styles import section_title, stat_card
from fitfusion import db, pose_detection, videos
from fitfusion.workout_engine import EXERCISES

st.set_page_config(page_title=f"{t('trainer_title')} · FitFusion", page_icon="🕺", layout="centered")
user = require_login()

st.title(f"🕺 {t('trainer_title')}")

default_idx = 0
day_exercises = st.session_state.get("trainer_day_exercises")
if day_exercises:
    wanted_ids = {d["id"] for d in day_exercises}
    for i, ex in enumerate(EXERCISES):
        if ex["id"] in wanted_ids:
            default_idx = i
            break

exercise = st.selectbox(t("select_exercise"), EXERCISES, index=default_idx, format_func=lambda e: e["name"])
trackable = exercise["id"] in pose_detection.EXERCISE_ANGLES

col_a, col_b = st.columns(2)
with col_a:
    section_title("🎯", t("target_muscles"))
    st.write(", ".join(m.replace("_", " ").title() for m in exercise["muscles"]))
    st.caption(f"{t('difficulty')}: {exercise['difficulty'].title()}")
with col_b:
    section_title("🎬", t("watch_demo"))
    st.link_button(f"▶️ {t('watch_demo')}", videos.get_demo_video_url(exercise["id"], exercise["name"]), use_container_width=True)

cal_per_min = exercise["cal_per_min"]

st.divider()
section_title("📷", t("start_camera"))

if "trainer_start_time" not in st.session_state:
    st.session_state["trainer_start_time"] = None

use_camera = False
if pose_detection.POSE_AVAILABLE and trackable:
    use_camera = st.toggle(f"📷 {t('use_camera_toggle')}", value=False, key="use_camera_toggle")
elif not trackable:
    st.caption(t("camera_not_trackable"))
else:
    st.warning(t("camera_unavailable"))

if use_camera:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration

    RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
    ctx = webrtc_streamer(
        key="ff-pose-trainer",
        video_processor_factory=lambda: pose_detection.RepCounterProcessor(exercise["id"]),
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={"video": True, "audio": False},
    )

    if ctx.video_processor:
        ctx.video_processor.set_exercise(exercise["id"])
        if ctx.state.playing and st.session_state["trainer_start_time"] is None:
            st.session_state["trainer_start_time"] = time.time()

    metrics_ph = st.empty()

    @st.fragment(run_every=1)
    def live_stats():
        elapsed_min = 0.0
        reps = 0
        accuracy = 0.0
        if ctx.state.playing and ctx.video_processor and st.session_state["trainer_start_time"]:
            snap = ctx.video_processor.snapshot()
            reps = snap["reps"]
            accuracy = snap["accuracy"]
            elapsed_min = (time.time() - st.session_state["trainer_start_time"]) / 60
        calories = round(elapsed_min * cal_per_min, 1)
        target_reps = 12
        completion = min(100, round(reps / target_reps * 100)) if target_reps else 0

        with metrics_ph.container():
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t("rep_counter"), reps)
            m2.metric(t("accuracy_score"), f"{accuracy}%")
            m3.metric(t("workout_timer"), f"{elapsed_min:.1f} min")
            m4.metric(t("calories_burned"), f"{calories} {t('kcal')}")
            st.progress(completion / 100, text=f"{t('completion_pct')}: {completion}%")

    live_stats()

    if st.button(f"✅ {t('start_workout')}", key="log_camera_workout", use_container_width=True, type="primary"):
        snap = ctx.video_processor.snapshot() if ctx.video_processor else {"reps": 0, "accuracy": 0}
        elapsed = ((time.time() - st.session_state["trainer_start_time"]) / 60) if st.session_state["trainer_start_time"] else 0
        db.log_workout(user["id"], exercise["name"], sets=1, reps=snap["reps"], duration_min=round(elapsed, 1),
                        calories_burned=round(elapsed * cal_per_min, 1), accuracy_score=snap["accuracy"])
        st.session_state["trainer_start_time"] = None
        st.success(t("success_saved"))
        st.balloons()
else:
    st.markdown(f"**{t('manual_rep_counter')}**")
    if "manual_reps" not in st.session_state:
        st.session_state["manual_reps"] = 0
    mc1, mc2, mc3 = st.columns(3)
    if mc1.button("➖", use_container_width=True):
        st.session_state["manual_reps"] = max(0, st.session_state["manual_reps"] - 1)
    mc2.markdown(f"<h2 style='text-align:center'>{st.session_state['manual_reps']}</h2>", unsafe_allow_html=True)
    if mc3.button("➕", use_container_width=True):
        st.session_state["manual_reps"] += 1

    duration = st.slider(t("duration") + " (min)", 1, 60, 5)
    calories = round(duration * cal_per_min, 1)
    stat_card("🔥", t("calories_burned"), f"{calories} {t('kcal')}")

    if st.button(f"✅ {t('start_workout')}", use_container_width=True, type="primary"):
        db.log_workout(user["id"], exercise["name"], sets=1, reps=st.session_state["manual_reps"],
                        duration_min=duration, calories_burned=calories, accuracy_score=None)
        st.session_state["manual_reps"] = 0
        st.success(t("success_saved"))
        st.balloons()
