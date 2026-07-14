import collections
import datetime as dt

import streamlit as st

from fitfusion.i18n import t
from fitfusion.nav import require_login
from fitfusion.styles import section_title, stat_card, glass_card, empty_state
from fitfusion.charts import line_trend, bar_weekly, dual_line
from fitfusion import db, achievements as ach

st.set_page_config(page_title=f"{t('progress_title')} · FitFusion", page_icon="📈", layout="centered")
user = require_login()

st.title(f"📈 {t('progress_title')}")

wc1, wc2, wc3, wc4 = st.columns([2, 1, 2, 1])
with wc1:
    new_weight = st.number_input(t("log_weight"), 30.0, 300.0, float(db.get_profile(user["id"])["weight_kg"] or 70), label_visibility="visible")
with wc2:
    st.write("")
    st.write("")
    if st.button(t("log_weight"), use_container_width=True, type="primary"):
        db.log_weight(user["id"], new_weight)
        st.success(t("success_saved"))
        st.rerun()
with wc3:
    new_sleep = st.number_input(t("log_sleep_hours"), 0.0, 14.0, 7.0, step=0.5, label_visibility="visible")
with wc4:
    st.write("")
    st.write("")
    if st.button(t("log_sleep"), use_container_width=True, type="primary"):
        db.log_sleep(user["id"], new_sleep)
        st.success(t("success_saved"))
        st.rerun()

weights = db.weight_logs(user["id"])
analyses = db.all_body_analyses(user["id"])

section_title("⚖️", t("weight_history"))
if weights:
    st.plotly_chart(line_trend([w["date"] for w in weights], [w["weight_kg"] for w in weights], t("weight_history")), use_container_width=True, config={"displayModeBar": False})
else:
    empty_state(t("empty_no_data"))

c1, c2 = st.columns(2)
with c1:
    section_title("📐", t("bmi_trend"))
    if analyses:
        st.plotly_chart(line_trend([a["created_at"][:10] for a in analyses], [a["bmi"] for a in analyses], t("bmi_trend"), "#4CB7C5"), use_container_width=True, config={"displayModeBar": False})
    else:
        empty_state(t("empty_no_data"))
with c2:
    section_title("🧈", t("body_fat_trend"))
    if analyses:
        st.plotly_chart(line_trend([a["created_at"][:10] for a in analyses], [a["body_fat_estimate"] for a in analyses], t("body_fat_trend"), "#8BC53F"), use_container_width=True, config={"displayModeBar": False})
    else:
        empty_state(t("empty_no_data"))

section_title("🔥", t("calories_burned_vs_consumed"))
workouts = db.workout_logs(user["id"])
meals = db.all_meals(user["id"])
if workouts or meals:
    burned_by_day = collections.defaultdict(float)
    for w in workouts:
        burned_by_day[w["date"]] += w["calories_burned"] or 0
    consumed_by_day = collections.defaultdict(float)
    for m in meals:
        consumed_by_day[m["date"]] += m["calories"] or 0
    all_dates = sorted(set(burned_by_day) | set(consumed_by_day))
    st.plotly_chart(
        dual_line(all_dates, [consumed_by_day[d] for d in all_dates], [burned_by_day[d] for d in all_dates], "Consumed", "Burned"),
        use_container_width=True, config={"displayModeBar": False},
    )
else:
    empty_state(t("empty_no_data"))

section_title("📅", t("weekly_activity"))
if workouts:
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())
    minutes_by_day = collections.defaultdict(float)
    for w in workouts:
        d = dt.date.fromisoformat(w["date"])
        if d >= week_start:
            minutes_by_day[d.strftime("%a")] += w["duration_min"] or 0
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    st.plotly_chart(bar_weekly(day_order, [minutes_by_day.get(d, 0) for d in day_order], "Minutes"), use_container_width=True, config={"displayModeBar": False})
else:
    empty_state(t("empty_no_data"))

section_title("😴", t("sleep_stats"))
sleep_rows = db.sleep_logs(user["id"])
if sleep_rows:
    st.plotly_chart(line_trend([s["date"] for s in sleep_rows], [s["hours"] for s in sleep_rows], t("sleep_stats"), "#4CB7C5"), use_container_width=True, config={"displayModeBar": False})
else:
    empty_state(t("empty_no_data"))

c3, c4, c5 = st.columns(3)
with c3:
    stat_card("🔥", t("streaks"), f"{db.workout_streak(user['id'])} {t('days')}")
with c4:
    best_calories = max([w["calories_burned"] or 0 for w in workouts], default=0)
    stat_card("🏆", t("personal_records"), f"{round(best_calories)} {t('kcal')}")
with c5:
    stat_card("💪", t("workout_history"), str(len(workouts)))

section_title("🏆", t("achievements"))
unlocked = ach.evaluate_and_unlock(user["id"])
if unlocked:
    cols = st.columns(4)
    for i, a in enumerate(unlocked):
        with cols[i % 4]:
            glass_card(f"<div style='text-align:center;font-size:30px'>{a['icon']}</div><p style='text-align:center;font-size:12px'>{a['title']}</p>", glow="gold")
else:
    empty_state(t("empty_no_data"), "🏆")
