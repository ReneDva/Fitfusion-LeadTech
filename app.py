"""FitFusion — AI Fitness & Nutrition Platform.

Entry point: auth -> profile setup -> dashboard (Home).
Run with:  streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from fitfusion.config import APP_NAME, ACTIVITY_LEVELS, FITNESS_GOALS, DIETARY_PREFERENCES, EXPERIENCE_LEVELS, WORKOUT_LOCATIONS, SUPPORTED_LANGUAGES, GOLD, BLUE
from fitfusion.i18n import t, current_language, set_language
from fitfusion.styles import app_shell_open, glass_card, stat_card, section_title, gold_glow_logo, LOGO_PATH
from fitfusion.nav import render_sidebar, render_language_picker
from fitfusion import db, auth, calculations, workout_engine
from fitfusion.charts import progress_ring

_page_icon = "💪"
if LOGO_PATH.exists():
    from PIL import Image
    _page_icon = Image.open(LOGO_PATH)

if "stage" not in st.session_state:
    st.session_state["stage"] = "auth"

# Sidebar nav is only useful once there's somewhere to navigate to — keep it out of the
# way during auth, but default it open once the user is past login.
_sidebar_state = "expanded" if st.session_state["stage"] in ("profile_setup", "dashboard") else "collapsed"
st.set_page_config(page_title=APP_NAME, page_icon=_page_icon, layout="centered", initial_sidebar_state=_sidebar_state)
app_shell_open()

# Benefit blurbs shown on the signup tab (was previously a multi-screen onboarding tour).
ONBOARDING_PAGES = [
    ("🤖", "onboarding_title_1", "onboarding_body_1"),
    ("🥗", "onboarding_title_2", "onboarding_body_2"),
    ("🧬", "onboarding_title_3", "onboarding_body_3"),
    ("🕺", "onboarding_title_4", "onboarding_body_4"),
    ("📈", "onboarding_title_5", "onboarding_body_5"),
]


# ------------------------------------------------------------------ AUTH ----
def render_auth():
    st.markdown(gold_glow_logo(80), unsafe_allow_html=True)
    _, lang_col, _ = st.columns([1, 2, 1])
    with lang_col:
        render_language_picker(key="auth_lang_selector")

    tab_login, tab_signup = st.tabs([t("login_button"), t("signup_button")])

    with tab_login:
        st.subheader(t("login_title"))
        st.caption(t("login_subtitle"))
        with st.form("login_form"):
            identifier = st.text_input(f"{t('email')} / {t('username')}")
            password = st.text_input(t("password"), type="password")
            submitted = st.form_submit_button(t("login_button"), width='stretch', type="primary")
        if submitted:
            user, error = auth.login(identifier, password)
            if error:
                st.error(t(error))
            else:
                st.session_state["user_id"] = user["id"]
                profile = db.get_profile(user["id"])
                if profile and profile["language"]:
                    set_language(profile["language"])
                st.session_state["stage"] = "dashboard" if profile and profile["onboarded"] else "profile_setup"
                st.rerun()
        st.divider()
        oc1, oc2 = st.columns(2)
        if oc1.button(t("continue_google"), width='stretch'):
            st.info("Google Sign-In needs a registered OAuth app — not wired up in this local build. Please use email/password.")
        if oc2.button(t("continue_apple"), width='stretch'):
            st.info("Apple Sign-In needs a registered OAuth app — not wired up in this local build. Please use email/password.")

    with tab_signup:
        st.subheader(t("signup_title"))
        st.caption(t("signup_subtitle"))

        for icon, title_key, body_key in ONBOARDING_PAGES:
            st.markdown(
                f"<div style='display:flex;align-items:flex-start;gap:10px;margin-bottom:10px'>"
                f"<span style='font-size:22px'>{icon}</span>"
                f"<div><b>{t(title_key)}</b><br>"
                f"<span style='color:#B3B3B3;font-size:13.5px'>{t(body_key)}</span></div></div>",
                unsafe_allow_html=True,
            )
        st.divider()

        with st.form("signup_form"):
            name = st.text_input(t("name"))
            email = st.text_input(t("email"))
            username = st.text_input(t("username"))
            password = st.text_input(t("password"), type="password")
            confirm = st.text_input(t("confirm_password"), type="password")
            submitted = st.form_submit_button(t("signup_button"), width='stretch', type="primary")
        if submitted:
            if password != confirm:
                st.error(t("passwords_dont_match"))
            else:
                user_id, error = auth.signup(email, username, name, password)
                if error:
                    st.error(t(error))
                else:
                    st.session_state["user_id"] = user_id
                    db.update_profile(user_id, language=current_language())
                    st.session_state["stage"] = "profile_setup"
                    st.success(t("success_saved"))
                    st.rerun()


# ------------------------------------------------------------ PROFILE SETUP ----
def render_profile_setup():
    st.header(t("profile_setup_title"))
    st.caption(t("profile_setup_subtitle"))
    with st.form("profile_setup_form"):
        lang_codes = list(SUPPORTED_LANGUAGES.keys())
        lang_labels = [f"{SUPPORTED_LANGUAGES[c]['flag']} {SUPPORTED_LANGUAGES[c]['label']}" for c in lang_codes]
        lang_idx = lang_codes.index(current_language()) if current_language() in lang_codes else 0
        language_choice = st.selectbox(t("language_settings"), lang_labels, index=lang_idx)

        c1, c2 = st.columns(2)
        height = c1.number_input(t("height_cm"), 100.0, 250.0, 170.0)
        weight = c2.number_input(t("weight_kg"), 30.0, 300.0, 70.0)
        age = c1.number_input(t("age"), 13, 100, 28)
        gender = c2.selectbox(t("gender"), ["male", "female", "other"], format_func=lambda g: t(g))

        activity = st.selectbox(t("activity_level"), ACTIVITY_LEVELS, format_func=lambda a: t(f"activity_{a}"))
        goal = st.selectbox(t("fitness_goal"), FITNESS_GOALS, format_func=lambda g: t(f"goal_{g}"))
        experience = st.selectbox(t("experience_level"), EXPERIENCE_LEVELS, format_func=lambda e: t(f"experience_{e}"))

        c3, c4 = st.columns(2)
        body_fat = c3.number_input(t("body_fat_pct"), 0.0, 60.0, 0.0)
        muscle_mass = c4.number_input(t("muscle_mass_kg"), 0.0, 100.0, 0.0)

        dietary = st.selectbox(t("dietary_preference"), DIETARY_PREFERENCES, format_func=lambda d: t(f"diet_{d}"))
        allergies = st.text_input(t("food_allergies"))
        medical = st.text_input(t("medical_limitations"))

        st.markdown(f"**{t('workout_location')} & {t('equipment')}**")
        location = st.selectbox(t("workout_location"), WORKOUT_LOCATIONS, format_func=lambda l: t(f"location_{l}"))
        equipment = st.multiselect(
            t("equipment"),
            ["dumbbells", "barbell", "bench", "resistance_band", "pull_up_bar", "machine", "kettlebell", "jump_rope", "bike"],
            format_func=lambda e: t(f"equip_{e}"),
            placeholder=t("choose_options"),
        )
        c5, c6 = st.columns(2)
        days_per_week = c5.slider(t("workout_days_per_week"), 1, 7, 3)
        session_minutes = c6.slider(t("session_minutes"), 15, 90, 30)

        submitted = st.form_submit_button(t("save_continue"), width='stretch', type="primary")

    if submitted:
        chosen_language = lang_codes[lang_labels.index(language_choice)]
        set_language(chosen_language)

        profile_fields = dict(
            height_cm=height, weight_kg=weight, age=int(age), gender=gender,
            activity_level=activity, fitness_goal=goal, experience_level=experience,
            body_fat_pct=body_fat or None, muscle_mass_kg=muscle_mass or None,
            dietary_preference=dietary, food_allergies=allergies, medical_limitations=medical,
            workout_location=location, equipment=str(equipment).replace("'", '"'),
            workout_days_per_week=days_per_week, session_minutes=session_minutes,
            language=chosen_language, onboarded=1,
        )
        db.update_profile(st.session_state["user_id"], **profile_fields)

        analysis_input = dict(profile_fields)
        result = calculations.full_body_analysis(analysis_input)
        db.save_body_analysis(st.session_state["user_id"], result)

        plan_input = dict(profile_fields, equipment=equipment)
        plan = workout_engine.generate_plan(plan_input, st.session_state["user_id"])
        db.save_workout_plan(st.session_state["user_id"], goal, plan)

        st.session_state["stage"] = "dashboard"
        st.success(t("success_saved"))
        st.rerun()


# --------------------------------------------------------------- DASHBOARD ----
def render_dashboard():
    render_sidebar()
    user, profile = db.get_user(st.session_state["user_id"]), db.get_profile(st.session_state["user_id"])

    st.markdown(f"### {t('dashboard_greeting', name=user['name'])}")
    st.markdown(f"<p style='color:#B3B3B3;font-style:italic'>&ldquo;{t('daily_quote')}&rdquo;</p>", unsafe_allow_html=True)

    analysis = db.latest_body_analysis(user["id"])
    daily_calories = analysis["daily_calories"] if analysis else 2000
    meals_today = db.meals_for_date(user["id"])
    consumed = sum(m["calories"] for m in meals_today)
    remaining = max(0, daily_calories - consumed)
    water_cups = db.water_today(user["id"])
    streak = db.workout_streak(user["id"])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(progress_ring(consumed, daily_calories, t("calories_goal"), GOLD), width='stretch', config={"displayModeBar": False})
    with c2:
        st.plotly_chart(progress_ring(water_cups, 8, t("water_intake"), BLUE), width='stretch', config={"displayModeBar": False})
    with c3:
        activity_score = min(100, streak * 15 + (20 if meals_today else 0))
        st.plotly_chart(progress_ring(activity_score, 100, t("activity_score"), "#8BC53F"), width='stretch', config={"displayModeBar": False})

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        stat_card("🔥", t("workout_streak"), f"{streak} {t('days')}")
    with b2:
        sleep_rows = db.sleep_logs(user["id"])
        last_sleep = sleep_rows[-1]["hours"] if sleep_rows else 0
        stat_card("😴", t("sleep_summary"), f"{last_sleep} h")
    with b3:
        goal_label = t(f"goal_{profile['fitness_goal']}") if profile and profile["fitness_goal"] else "-"
        stat_card("🧬", t("body_status"), goal_label)
    with b4:
        stat_card("🥇", t("metabolic_score"), str(analysis["metabolic_score"]) if analysis else "-")

    wc1, wc2 = st.columns(2)
    with wc1:
        if st.button(f"💧 {t('log_water')}", width='stretch'):
            db.log_water(user["id"], 1)
            st.rerun()
    with wc2:
        hours = st.number_input(t("log_sleep"), 0.0, 14.0, 7.0, step=0.5, label_visibility="collapsed")
        if st.button(f"😴 {t('log_sleep')}", width='stretch'):
            db.log_sleep(user["id"], hours)
            st.rerun()

    section_title("🎯", t("weekly_challenge"))
    glass_card(f"<b>{t('goal_general_health')}:</b> {t('log_water')} 8/8, {t('workout_streak')} 3+ {t('days')}", glow="green")

    section_title("✨", "Premium AI Features")
    p1, p2 = st.columns(2)
    with p1:
        glass_card(
            f"<h4 style='color:{BLUE};margin-top:0'>🤖 {t('ai_coach_card_title')}</h4>"
            f"<p style='color:#B3B3B3'>{t('ai_coach_card_body')}</p>",
            glow="blue",
        )
        st.page_link("pages/5_🤖_AI_Coach.py", label=t("chat_with_ai_coach"), icon="🤖")
    with p2:
        glass_card(
            f"<h4 style='color:{GOLD};margin-top:0'>🧬 {t('ai_body_analysis_card_title')}</h4>"
            f"<p style='color:#B3B3B3'>{t('ai_body_analysis_card_body')}</p>",
            glow="gold",
        )
        st.page_link("pages/1_🧬_Body_Analysis.py", label=t("analyze_my_body"), icon="🧬")

    st.divider()
    st.caption(t("nav_hint"))


# ---------------------------------------------------------------- ROUTER ----
stage = st.session_state["stage"]
if stage == "auth":
    render_auth()
elif stage == "profile_setup":
    render_profile_setup()
else:
    render_dashboard()
