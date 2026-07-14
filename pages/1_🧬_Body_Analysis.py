import streamlit as st

from fitfusion.config import ACTIVITY_LEVELS, FITNESS_GOALS, GOLD, BLUE, GREEN
from fitfusion.i18n import t, current_language
from fitfusion.nav import require_login
from fitfusion.styles import section_title, stat_card, glass_card
from fitfusion.charts import progress_ring, macro_donut
from fitfusion import db, calculations, ai

st.set_page_config(page_title=f"{t('body_analysis_title')} · FitFusion", page_icon="🧬", layout="centered")
user = require_login()
profile = db.get_profile(user["id"])

st.title(f"🧬 {t('body_analysis_title')}")
st.caption(t("body_analysis_subtitle"))

with st.form("body_analysis_form"):
    c1, c2 = st.columns(2)
    height = c1.number_input(t("height_cm"), 100.0, 250.0, float(profile["height_cm"] or 170))
    weight = c2.number_input(t("weight_kg"), 30.0, 300.0, float(profile["weight_kg"] or 70))
    age = c1.number_input(t("age"), 13, 100, int(profile["age"] or 28))
    gender = c2.selectbox(t("gender"), ["male", "female", "other"],
                           index=["male", "female", "other"].index(profile["gender"] or "male"),
                           format_func=lambda g: t(g))
    activity = st.selectbox(t("activity_level"), ACTIVITY_LEVELS,
                             index=ACTIVITY_LEVELS.index(profile["activity_level"] or "moderate"),
                             format_func=lambda a: t(f"activity_{a}"))
    goal = st.selectbox(t("fitness_goal"), FITNESS_GOALS,
                         index=FITNESS_GOALS.index(profile["fitness_goal"] or "general_health"),
                         format_func=lambda g: t(f"goal_{g}"))
    c3, c4 = st.columns(2)
    body_fat = c3.number_input(t("body_fat_pct"), 0.0, 60.0, float(profile["body_fat_pct"] or 0.0))
    sleep_hours = c4.number_input(t("avg_sleep_hours"), 0.0, 14.0, 7.0)
    submitted = st.form_submit_button(t("run_analysis"), use_container_width=True, type="primary")

if submitted:
    with st.spinner(t("analyzing")):
        profile_input = dict(
            height_cm=height, weight_kg=weight, age=int(age), gender=gender,
            activity_level=activity, fitness_goal=goal,
            body_fat_pct=body_fat or None, experience_level=profile["experience_level"],
            sleep_hours=sleep_hours,
        )
        result = calculations.full_body_analysis(profile_input)
        db.save_body_analysis(user["id"], result)
        db.update_profile(user["id"], height_cm=height, weight_kg=weight, age=int(age), gender=gender,
                           activity_level=activity, fitness_goal=goal, body_fat_pct=body_fat or None)
        st.session_state["last_analysis"] = result
    st.success(t("success_saved"))

result = st.session_state.get("last_analysis")
if not result:
    latest = db.latest_body_analysis(user["id"])
    result = dict(latest) if latest else None

if result:
    st.divider()
    section_title("📊", t("results_title"))

    c1, c2, c3 = st.columns(3)
    with c1:
        stat_card("⚖️", t("bmi"), str(result["bmi"]))
    with c2:
        stat_card("🎯", t("healthy_weight_range"), f"{result['healthy_weight_min']}-{result['healthy_weight_max']} {t('kg')}")
    with c3:
        stat_card("🧈", t("body_fat_estimate"), f"{result['body_fat_estimate']}%")

    c4, c5, c6 = st.columns(3)
    with c4:
        stat_card("🔥", t("bmr"), f"{int(result['bmr'])} {t('kcal')}", color=BLUE)
    with c5:
        stat_card("⚡", t("tdee"), f"{int(result['tdee'])} {t('kcal')}", color=BLUE)
    with c6:
        stat_card("🍽️", t("daily_calories"), f"{int(result['daily_calories'])} {t('kcal')}", color=GOLD)

    mc1, mc2 = st.columns(2)
    with mc1:
        st.plotly_chart(
            macro_donut(result["protein_g"], result["carbs_g"], result["fat_g"]),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.caption(f"{t('protein')}: {int(result['protein_g'])}{t('g')} · {t('carbs')}: {int(result['carbs_g'])}{t('g')} · {t('fat')}: {int(result['fat_g'])}{t('g')}")
    with mc2:
        st.plotly_chart(
            progress_ring(result["metabolic_score"], 100, t("metabolic_score"), GREEN),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.caption(f"💧 {t('water_target')}: {int(result['water_target_ml'])} {t('ml')}")

    c7, c8 = st.columns(2)
    with c7:
        stat_card("🧍", t("body_type"), result["body_type"].title())
    with c8:
        stat_card("📶", t("fitness_level"), result["fitness_level"].title())

    section_title("💡", t("recommendations"))
    recs = result.get("recommendations")
    if isinstance(recs, str):
        import json
        recs = json.loads(recs)
    for rec in recs or []:
        glass_card(f"✅ {rec}")

    if ai.ai_enabled():
        with st.spinner(t("loading_ai")):
            narrative = ai.narrate_body_analysis(result, current_language())
        if narrative:
            glass_card(f"🤖 <i>{narrative}</i>", glow="blue")
    else:
        st.info(t("ai_disabled_notice"))
else:
    st.info(t("empty_no_data"))
