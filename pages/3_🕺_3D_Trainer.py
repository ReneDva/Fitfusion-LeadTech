import time

import streamlit as st

from fitfusion.i18n import t
from fitfusion.nav import require_login
from fitfusion.styles import section_title, glass_card, stat_card
from fitfusion import db, skeleton3d, pose_detection
from fitfusion.workout_engine import EXERCISES

st.set_page_config(page_title=f"{t('trainer_title')} · FitFusion", page_icon="🕺", layout="centered")
user = require_login()

st.title(f"🕺 {t('trainer_title')}")

available = skeleton3d.available_exercises()
default_idx = 0
day_exercises = st.session_state.get("trainer_day_exercises")
if day_exercises:
    for i, ex in enumerate(available):
        if any(ex in d["id"] for d in day_exercises):
            default_idx = i
            break

exercise = st.selectbox(t("select_exercise"), available, index=default_idx, format_func=lambda e: e.replace("_", " ").title())
info = skeleton3d.exercise_info(exercise)

col_a, col_b = st.columns([3, 2])
with col_a:
    st.plotly_chart(skeleton3d.build_figure(exercise), use_container_width=True, config={"displayModeBar": False})
    st.caption(f"🔄 {t('rotate_hint')}")
with col_b:
    section_title("🎯", t("target_muscles"))
    st.write(", ".join(m.replace("_", " ").title() for m in info["muscles"]))
    section_title("💬", "Coach Cue")
    st.info(info["cue"])

cal_per_min = next((e["cal_per_min"] for e in EXERCISES if e["id"] == exercise), 8)

st.divider()
section_title("📷", t("start_camera"))

if "trainer_start_time" not in st.session_state:
    st.session_state["trainer_start_time"] = None

if pose_detection.POSE_AVAILABLE:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration

    RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
    ctx = webrtc_streamer(
        key="ff-pose-trainer",
        video_processor_factory=lambda: pose_detection.RepCounterProcessor(exercise),
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={"video": True, "audio": False},
    )

    if ctx.video_processor:
        ctx.video_processor.set_exercise(exercise)
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
        db.log_workout(user["id"], exercise, sets=1, reps=snap["reps"], duration_min=round(elapsed, 1),
                        calories_burned=round(elapsed * cal_per_min, 1), accuracy_score=snap["accuracy"])
        st.session_state["trainer_start_time"] = None
        st.success(t("success_saved"))
        st.balloons()
else:
    st.warning(t("camera_unavailable"))

    st.markdown(f"**Manual {t('rep_counter')}**")
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
        db.log_workout(user["id"], exercise, sets=1, reps=st.session_state["manual_reps"],
                        duration_min=duration, calories_burned=calories, accuracy_score=None)
        st.session_state["manual_reps"] = 0
        st.success(t("success_saved"))
        st.balloons()
