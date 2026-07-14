import streamlit as st

from fitfusion.i18n import t, current_language
from fitfusion.nav import require_login
from fitfusion import db, ai

st.set_page_config(page_title=f"{t('ai_coach_title')} · FitFusion", page_icon="🤖", layout="centered")
user = require_login()
profile = db.get_profile(user["id"])
analysis = db.latest_body_analysis(user["id"])

st.title(f"🤖 {t('ai_coach_title')}")

if not ai.ai_enabled():
    st.info(t("ai_disabled_notice"))

history_rows = db.conversation_history(user["id"])
for row in history_rows:
    with st.chat_message("user" if row["role"] == "user" else "assistant"):
        st.markdown(row["content"])

prompt = st.chat_input(t("ai_coach_placeholder"))
if prompt:
    db.save_message(user["id"], "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    context_parts = []
    if profile:
        if profile["fitness_goal"]:
            context_parts.append(f"goal: {profile['fitness_goal']}")
        if profile["dietary_preference"]:
            context_parts.append(f"diet: {profile['dietary_preference']}")
        if profile["food_allergies"]:
            context_parts.append(f"allergies: {profile['food_allergies']}")
        if profile["medical_limitations"]:
            context_parts.append(f"medical limitations: {profile['medical_limitations']}")
    if analysis:
        context_parts.append(f"BMI {analysis['bmi']}, fitness level {analysis['fitness_level']}, daily calorie target {int(analysis['daily_calories'])}")
    context = "; ".join(context_parts)

    history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

    with st.chat_message("assistant"):
        with st.spinner(t("ai_thinking")):
            reply = ai.chat_with_coach(prompt, history, current_language(), context)
        st.markdown(reply)
    db.save_message(user["id"], "assistant", reply)
