"""Shared sidebar chrome + auth guard used by app.py and every page in pages/."""
import streamlit as st

from fitfusion.config import APP_NAME, SUPPORTED_LANGUAGES
from fitfusion.i18n import t, current_language, set_language
from fitfusion.styles import app_shell_open
from fitfusion.db import get_user, get_profile, get_subscription


def require_login():
    app_shell_open()
    if not st.session_state.get("user_id"):
        st.warning("Please log in first.")
        st.page_link("app.py", label="⬅ " + t("login_button"))
        st.stop()
    render_sidebar()
    return get_user(st.session_state["user_id"])


def render_sidebar():
    user_id = st.session_state.get("user_id")
    with st.sidebar:
        st.markdown(f"### 💪 {APP_NAME}")
        if user_id:
            user = get_user(user_id)
            sub = get_subscription(user_id)
            plan_label = t("premium_plan") if sub and sub["plan"] == "premium" else t("free_plan")
            st.caption(f"{user['name']} · {plan_label}")

        lang_codes = list(SUPPORTED_LANGUAGES.keys())
        current = current_language()
        labels = [f"{SUPPORTED_LANGUAGES[c]['flag']} {SUPPORTED_LANGUAGES[c]['label']}" for c in lang_codes]
        idx = lang_codes.index(current) if current in lang_codes else 0
        choice = st.selectbox(t("language_settings"), labels, index=idx, key="lang_selector")
        chosen_code = lang_codes[labels.index(choice)]
        if chosen_code != current:
            set_language(chosen_code)
            st.rerun()

        st.divider()
        if user_id and st.button(t("logout"), use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def current_user_and_profile():
    user_id = st.session_state["user_id"]
    return get_user(user_id), get_profile(user_id)
