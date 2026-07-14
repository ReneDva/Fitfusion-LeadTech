import streamlit as st

from fitfusion.config import ACTIVITY_LEVELS, FITNESS_GOALS, DIETARY_PREFERENCES
from fitfusion.i18n import t
from fitfusion.nav import require_login
from fitfusion.styles import section_title, stat_card, glass_card
from fitfusion import db, achievements as ach

st.set_page_config(page_title=f"{t('profile_title')} · FitFusion", page_icon="👤", layout="centered")
user = require_login()
profile = db.get_profile(user["id"])
subscription = db.get_subscription(user["id"])

st.title(f"👤 {t('profile_title')}")

st.markdown(
    f"<div style='text-align:center;font-size:70px'>🧑‍🚀</div>"
    f"<h3 style='text-align:center;margin-top:0'>{user['name']}</h3>"
    f"<p style='text-align:center;color:#B3B3B3'>{user['email']}</p>",
    unsafe_allow_html=True,
)

plan = subscription["plan"] if subscription else "free"
plan_label = t("premium_plan") if plan == "premium" else t("free_plan")
plan_color = "#F4B223" if plan == "premium" else "#8BC53F"
glass_card(f"<b>{t('subscription_status')}:</b> <span style='color:{plan_color}'>{plan_label}</span>", glow="gold" if plan == "premium" else "")
if plan != "premium":
    st.page_link("pages/8_✨_Premium.py", label=f"✨ {t('premium_title')}")

section_title("✏️", t("edit_profile"))
with st.form("edit_profile_form"):
    c1, c2 = st.columns(2)
    height = c1.number_input(t("height_cm"), 100.0, 250.0, float(profile["height_cm"] or 170))
    weight = c2.number_input(t("weight_kg"), 30.0, 300.0, float(profile["weight_kg"] or 70))
    activity = st.selectbox(t("activity_level"), ACTIVITY_LEVELS,
                             index=ACTIVITY_LEVELS.index(profile["activity_level"] or "moderate"),
                             format_func=lambda a: t(f"activity_{a}"))
    goal = st.selectbox(t("fitness_goal"), FITNESS_GOALS,
                         index=FITNESS_GOALS.index(profile["fitness_goal"] or "general_health"),
                         format_func=lambda g: t(f"goal_{g}"))
    dietary = st.selectbox(t("dietary_preference"), DIETARY_PREFERENCES,
                            index=DIETARY_PREFERENCES.index(profile["dietary_preference"] or "none"),
                            format_func=lambda d: d.replace("_", " ").title())
    allergies = st.text_input(t("food_allergies"), value=profile["food_allergies"] or "")
    if st.form_submit_button(t("save"), type="primary", use_container_width=True):
        db.update_profile(user["id"], height_cm=height, weight_kg=weight, activity_level=activity,
                           fitness_goal=goal, dietary_preference=dietary, food_allergies=allergies)
        st.success(t("success_saved"))
        st.rerun()

section_title("📊", "Progress Snapshot")
c1, c2, c3 = st.columns(3)
with c1:
    stat_card("🔥", t("workout_streak"), f"{db.workout_streak(user['id'])} {t('days')}")
with c2:
    stat_card("🏆", t("achievements"), str(len(db.achievements(user['id']))))
with c3:
    latest = db.latest_body_analysis(user["id"])
    stat_card("🥇", t("metabolic_score"), str(latest["metabolic_score"]) if latest else "-")

section_title("⚙️", t("notification_settings"))
st.caption("Local build: preferences are saved for this session. Real push notifications need a mobile app + notification service — see README roadmap.")
n1, n2, n3 = st.columns(3)
n1.checkbox("Workout Reminders", value=True, key="notif_workout")
n2.checkbox("Meal Reminders", value=True, key="notif_meals")
n3.checkbox("Water Reminders", value=True, key="notif_water")

section_title("🔒", t("privacy"))
st.caption("All your data (profile, meals, workouts, chat history) is stored locally in fitfusion.db on this machine — nothing is uploaded except AI requests (chat text / meal photos) sent to OpenAI when AI features are used.")

section_title("🌙", t("dark_mode"))
st.caption("FitFusion is a Dark Mode-only experience by design.")
st.toggle(t("dark_mode"), value=True, disabled=True)

st.divider()
if st.button(f"🚪 {t('logout')}", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
